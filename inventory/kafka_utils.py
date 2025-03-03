import json
import logging
from importlib import import_module
from confluent_kafka import Producer, Consumer, KafkaError
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

def get_kafka_producer():
    try:
        producer_config = {
            'bootstrap.servers': ','.join(settings.KAFKA_BOOTSTRAP_SERVERS),
            'client.id': 'laklak-producer',
            'retries': 5,
        }
        producer = Producer(producer_config)
        return producer
    except Exception as e:
        logger.error(f"Failed to create Kafka producer: {str(e)}")
        return None

def get_kafka_consumer(topic, group_id=None):
    try:
        consumer_config = {
            'bootstrap.servers': ','.join(settings.KAFKA_BOOTSTRAP_SERVERS),
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': True,
        }
        
        if group_id:
            consumer_config['group.id'] = group_id
        
        consumer = Consumer(consumer_config)
        consumer.subscribe([topic])
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
        
        topic = settings.KAFKA_TOPICS['INVENTORY_UPDATES']
        key = str(product_id).encode('utf-8') if product_id else None
        value = json.dumps(message).encode('utf-8')
        
        producer.produce(
            topic=topic,
            key=key,
            value=value,
            callback=delivery_report
        )
        
        producer.flush()
        
        if new_stock <= settings.LOW_STOCK_THRESHOLD:
            send_low_stock_alert(product_id, new_stock)
            
        return True
    except Exception as e:
        logger.error(f"Failed to send inventory update: {str(e)}")
        return False
    finally:
        # No need to close with confluent-kafka - it's handled during garbage collection
        pass

def delivery_report(err, msg):
    if err is not None:
        logger.error(f"Message delivery failed: {err}")
    else:
        logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}]")

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
        
        topic = settings.KAFKA_TOPICS['LOW_STOCK_ALERTS']
        key = str(product_id).encode('utf-8') if product_id else None
        value = json.dumps(message).encode('utf-8')
        
        producer.produce(
            topic=topic,
            key=key,
            value=value,
            callback=delivery_report
        )
        
        producer.flush()
        return True
    except Exception as e:
        logger.error(f"Failed to send low stock alert: {str(e)}")
        return False
    finally:
        # No need to close with confluent-kafka
        pass

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
        
        topic = settings.KAFKA_TOPICS['PRODUCT_PRICE_CHANGES']
        key = str(product_id).encode('utf-8') if product_id else None
        value = json.dumps(message).encode('utf-8')
        
        producer.produce(
            topic=topic,
            key=key,
            value=value,
            callback=delivery_report
        )
        
        producer.flush()
        return True
    except Exception as e:
        logger.error(f"Failed to send price change event: {str(e)}")
        return False
    finally:
        # No need to close with confluent-kafka
        pass

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
        
        topic = settings.KAFKA_TOPICS['PRODUCT_CREATED']
        key = str(product_id).encode('utf-8') if product_id else None
        value = json.dumps(message).encode('utf-8')
        
        producer.produce(
            topic=topic,
            key=key,
            value=value,
            callback=delivery_report
        )
        
        producer.flush()
        return True
    except Exception as e:
        logger.error(f"Failed to send product created event: {str(e)}")
        return False
    finally:
        # No need to close with confluent-kafka
        pass

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
        
        topic = settings.KAFKA_TOPICS['PRODUCT_DELETED']
        key = str(product_id).encode('utf-8') if product_id else None
        value = json.dumps(message).encode('utf-8')
        
        producer.produce(
            topic=topic,
            key=key,
            value=value,
            callback=delivery_report
        )
        
        producer.flush()
        return True
    except Exception as e:
        logger.error(f"Failed to send product deleted event: {str(e)}")
        return False
    finally:
        # No need to close with confluent-kafka
        pass