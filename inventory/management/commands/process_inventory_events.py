import json
import logging
import time
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from core.models import Product, CustomUser
from inventory.models import InventoryTransaction, LowStockAlert, PriceChangeLog
from confluent_kafka import Consumer, KafkaError
import threading
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Process inventory events from Kafka topics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--topic',
            type=str,
            help='Specific Kafka topic to consume (default: all inventory topics)',
            required=False
        )
        
    def handle(self, *args, **options):
        specific_topic = options.get('topic')
        
        if specific_topic:
            if specific_topic in settings.KAFKA_TOPICS.values():
                self.stdout.write(self.style.SUCCESS(f'Starting consumer for topic: {specific_topic}'))
                self.process_topic(specific_topic)
            else:
                self.stdout.write(self.style.ERROR(f'Unknown topic: {specific_topic}'))
                return
        else:
            self.stdout.write(self.style.SUCCESS('Starting consumers for all inventory topics'))
            
            with ThreadPoolExecutor(max_workers=len(settings.KAFKA_TOPICS)) as executor:
                futures = []
                for topic_name, topic in settings.KAFKA_TOPICS.items():
                    self.stdout.write(self.style.SUCCESS(f'Starting consumer for topic: {topic} ({topic_name})'))
                    futures.append(executor.submit(self.process_topic, topic))
                
                for future in futures:
                    try:
                        future.result()
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Consumer error: {str(e)}'))

    def process_topic(self, topic):
        try:
            consumer_config = {
                'bootstrap.servers': ','.join(settings.KAFKA_BOOTSTRAP_SERVERS),
                'group.id': f'inventory-processor-{topic}',
                'auto.offset.reset': 'earliest',
                'enable.auto.commit': True,
                'session.timeout.ms': 6000
            }
            
            consumer = Consumer(consumer_config)
            consumer.subscribe([topic])
            
            if not consumer:
                self.stdout.write(self.style.ERROR(f'Failed to create consumer for topic: {topic}'))
                return
            
            self.stdout.write(self.style.SUCCESS(f'Consumer started for topic: {topic}'))
            running = True
            
            try:
                while running:
                    msg = consumer.poll(1.0)
                    
                    if msg is None:
                        continue
                    
                    if msg.error():
                        if msg.error().code() == KafkaError._PARTITION_EOF:
                            # End of partition event
                            self.stdout.write(f'Reached end of topic {topic} partition {msg.partition()}')
                        else:
                            self.stdout.write(self.style.ERROR(f'Error: {msg.error()}'))
                    else:
                        try:
                            # Parse the message value
                            value = json.loads(msg.value().decode('utf-8'))
                            self.stdout.write(f'Processing message: {value}')
                            
                            # Process the message based on the topic
                            if topic == settings.KAFKA_TOPICS['INVENTORY_UPDATES']:
                                self.process_inventory_update(value)
                            elif topic == settings.KAFKA_TOPICS['LOW_STOCK_ALERTS']:
                                self.process_low_stock_alert(value)
                            elif topic == settings.KAFKA_TOPICS['PRODUCT_PRICE_CHANGES']:
                                self.process_price_change(value)
                            elif topic == settings.KAFKA_TOPICS['PRODUCT_CREATED']:
                                self.process_product_created(value)
                            elif topic == settings.KAFKA_TOPICS['PRODUCT_DELETED']:
                                self.process_product_deleted(value)
                            
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'Error processing message: {str(e)}'))
                            logger.error(f'Error processing message: {str(e)}', exc_info=True)
                        
                        time.sleep(0.1)
                    
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING('Stopping consumer due to keyboard interrupt'))
                running = False
            finally:
                consumer.close()
                self.stdout.write(self.style.SUCCESS(f'Consumer for topic {topic} closed'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error in process_topic: {str(e)}'))
            logger.error(f'Error in process_topic: {str(e)}', exc_info=True)

    def process_inventory_update(self, message):
        try:
            product_id = message.get('product_id')
            old_stock = message.get('old_stock')
            new_stock = message.get('new_stock')
            user_id = message.get('user_id')
            
            with transaction.atomic():
                product = Product.objects.get(id=product_id)
                user = CustomUser.objects.get(id=user_id) if user_id else None
                
                transaction_exists = InventoryTransaction.objects.filter(
                    product=product,
                    previous_stock=old_stock,
                    new_stock=new_stock,
                    timestamp__gte=timezone.now() - timezone.timedelta(minutes=5)
                ).exists()
                
                if not transaction_exists:
                    quantity = new_stock - old_stock
                    transaction_type = 'add' if quantity > 0 else 'remove' if quantity < 0 else 'adjust'
                    
                    InventoryTransaction.objects.create(
                        product=product,
                        quantity=abs(quantity) if transaction_type != 'adjust' else quantity,
                        previous_stock=old_stock,
                        new_stock=new_stock,
                        transaction_type=transaction_type,
                        notes='Created by Kafka event processor',
                        performed_by=user
                    )
                    
                    self.stdout.write(self.style.SUCCESS(
                        f'Created inventory transaction record for product {product.name} (ID: {product_id})'
                    ))
                
                if new_stock <= settings.LOW_STOCK_THRESHOLD:
                    existing_alert = LowStockAlert.objects.filter(
                        product_id=product_id,
                        status__in=['pending', 'acknowledged']
                    ).first()
                    
                    if not existing_alert:
                        LowStockAlert.objects.create(
                            product=product,
                            stock_level=new_stock,
                            threshold=settings.LOW_STOCK_THRESHOLD,
                            status='pending'
                        )
                        self.stdout.write(self.style.WARNING(
                            f'Created low stock alert for product {product.name} (ID: {product_id})'
                        ))
        except Exception as e:
            logger.error(f'Error processing inventory update: {str(e)}', exc_info=True)
            raise

    def process_low_stock_alert(self, message):
        try:
            product_id = message.get('product_id')
            current_stock = message.get('current_stock')
            threshold = message.get('threshold')
            
            self.stdout.write(self.style.WARNING(
                f'Low stock alert for product {product_id}: {current_stock} (threshold: {threshold})'
            ))
            
        except Exception as e:
            logger.error(f'Error processing low stock alert: {str(e)}', exc_info=True)
            raise

    def process_price_change(self, message):
        try:
            product_id = message.get('product_id')
            old_price = message.get('old_price')
            new_price = message.get('new_price')
            user_id = message.get('user_id')
            
            with transaction.atomic():
                product = Product.objects.get(id=product_id)
                user = CustomUser.objects.get(id=user_id) if user_id else None
                
                price_change_exists = PriceChangeLog.objects.filter(
                    product=product,
                    old_price=old_price,
                    new_price=new_price,
                    changed_at__gte=timezone.now() - timezone.timedelta(minutes=5)
                ).exists()
                
                if not price_change_exists:
                    PriceChangeLog.objects.create(
                        product=product,
                        old_price=old_price,
                        new_price=new_price,
                        changed_by=user,
                        notes='Created by Kafka event processor'
                    )
                    
                    self.stdout.write(self.style.SUCCESS(
                        f'Created price change log for product {product.name} (ID: {product_id})'
                    ))
            
            self.stdout.write(f'Processed price change for product {product_id}: {old_price} -> {new_price}')
            
        except Exception as e:
            logger.error(f'Error processing price change: {str(e)}', exc_info=True)
            raise

    def process_product_created(self, message):
        try:
            product_id = message.get('product_id')
            product_data = message.get('product_data')
            
            self.stdout.write(f'Processed product creation: {product_id}')
            
        except Exception as e:
            logger.error(f'Error processing product creation: {str(e)}', exc_info=True)
            raise

    def process_product_deleted(self, message):
        try:
            product_id = message.get('product_id')
            product_data = message.get('product_data')
            
            self.stdout.write(f'Processed product deletion: {product_id}')
            
        except Exception as e:
            logger.error(f'Error processing product deletion: {str(e)}', exc_info=True)
            raise