import json
import logging
from importlib import import_module
from kafka import KafkaProducer, KafkaConsumer
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

def get_kafka_producer():
    try:
        producer = KafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: str(k).encode('utf-8') if k else None,
            retries=5
        )
        return producer
    except Exception as e:
        logger.error(f"Failed to create Kafka producer: {str(e)}")
        return None

def get_kafka_consumer(topic, group_id=None):
    try:
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_deserializer=lambda v: json.loads(v.decode('utf-8')),
            auto_offset_reset='earliest',
            group_id=group_id,
            enable_auto_commit=True
        )
        return consumer
    except Exception as e:
        logger.error(f"Failed to create Kafka consumer for topic {topic}: {str(e)}")
        return None

def send_inventory_update(product_id, old_stock, new_stock, user_id=None):
    producer = get_kafka_producer()
    if not producer:
        logger.error("Cannot send inventory update: Kafka producer not available")
        return False
    
    try:
        message = {
            'product_id': product_id,
            'old_stock': old_stock,
            'new_stock': new_stock,
            'user_id': user_id,
            'timestamp': str(timezone.now())
        }
        
        future = producer.send(
            settings.KAFKA_TOPICS['INVENTORY_UPDATES'],
            key=product_id,
            value=message
        )
        
        future.get(timeout=10)
        producer.flush()
        
        if new_stock <= settings.LOW_STOCK_THRESHOLD:
            send_low_stock_alert(product_id, new_stock)
            
        return True
    except Exception as e:
        logger.error(f"Failed to send inventory update: {str(e)}")
        return False
    finally:
        producer.close()

def send_low_stock_alert(product_id, current_stock):
    producer = get_kafka_producer()
    if not producer:
        logger.error("Cannot send low stock alert: Kafka producer not available")
        return False
    
    try:
        message = {
            'product_id': product_id,
            'current_stock': current_stock,
            'threshold': settings.LOW_STOCK_THRESHOLD,
            'timestamp': str(timezone.now())
        }
        
        future = producer.send(
            settings.KAFKA_TOPICS['LOW_STOCK_ALERTS'],
            key=product_id,
            value=message
        )
        
        future.get(timeout=10)
        producer.flush()
        return True
    except Exception as e:
        logger.error(f"Failed to send low stock alert: {str(e)}")
        return False
    finally:
        producer.close()

def send_price_change_event(product_id, old_price, new_price, user_id=None):
    producer = get_kafka_producer()
    if not producer:
        logger.error("Cannot send price change event: Kafka producer not available")
        return False
    
    try:
        message = {
            'product_id': product_id,
            'old_price': str(old_price),
            'new_price': str(new_price),
            'user_id': user_id,
            'timestamp': str(timezone.now())
        }
        
        future = producer.send(
            settings.KAFKA_TOPICS['PRODUCT_PRICE_CHANGES'],
            key=product_id,
            value=message
        )
        
        future.get(timeout=10)
        producer.flush()
        return True
    except Exception as e:
        logger.error(f"Failed to send price change event: {str(e)}")
        return False
    finally:
        producer.close()

def send_product_created_event(product_id, product_data, user_id=None):
    producer = get_kafka_producer()
    if not producer:
        logger.error("Cannot send product created event: Kafka producer not available")
        return False
    
    try:
        message = {
            'product_id': product_id,
            'product_data': product_data,
            'user_id': user_id,
            'timestamp': str(timezone.now())
        }
        
        future = producer.send(
            settings.KAFKA_TOPICS['PRODUCT_CREATED'],
            key=product_id,
            value=message
        )
        
        future.get(timeout=10)
        producer.flush()
        return True
    except Exception as e:
        logger.error(f"Failed to send product created event: {str(e)}")
        return False
    finally:
        producer.close()

def send_product_deleted_event(product_id, product_data, user_id=None):
    producer = get_kafka_producer()
    if not producer:
        logger.error("Cannot send product deleted event: Kafka producer not available")
        return False
    
    try:
        message = {
            'product_id': product_id,
            'product_data': product_data,
            'user_id': user_id,
            'timestamp': str(timezone.now())
        }
        
        future = producer.send(
            settings.KAFKA_TOPICS['PRODUCT_DELETED'],
            key=product_id,
            value=message
        )
        
        future.get(timeout=10)
        producer.flush()
        return True
    except Exception as e:
        logger.error(f"Failed to send product deleted event: {str(e)}")
        return False
    finally:
        producer.close() 