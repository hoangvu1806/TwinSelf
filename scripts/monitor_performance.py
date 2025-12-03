import sys
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent))

from twinself import DigitalTwinChatbot
from qdrant_client import QdrantClient
from twinself.core.config import config


class PerformanceMonitor:
    """Monitor chatbot performance metrics."""
    
    def __init__(self, log_path: str = "./data/performance_logs.jsonl"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
    
    def log_metric(self, metric: Dict):
        """Log a performance metric."""
        metric['timestamp'] = datetime.now().isoformat()
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(metric, ensure_ascii=False) + '\n')
    
    def test_response_time(self, chatbot: DigitalTwinChatbot, queries: List[str]) -> Dict:
        """Test response time for multiple queries."""
        results = []
        
        for query in queries:
            start_time = time.time()
            try:
                response = chatbot.chat(query, context="", stream=False, save_history=False)
                elapsed = time.time() - start_time
                
                results.append({
                    'query': query,
                    'response_length': len(response),
                    'response_time': elapsed,
                    'success': True
                })
            except Exception as e:
                elapsed = time.time() - start_time
                results.append({
                    'query': query,
                    'response_time': elapsed,
                    'success': False,
                    'error': str(e)
                })
        
        avg_time = sum(r['response_time'] for r in results) / len(results)
        success_rate = sum(1 for r in results if r['success']) / len(results)
        
        return {
            'test': 'response_time',
            'queries_tested': len(queries),
            'avg_response_time': avg_time,
            'success_rate': success_rate,
            'results': results
        }
    
    def test_memory_retrieval(self, chatbot: DigitalTwinChatbot) -> Dict:
        """Test memory retrieval quality."""
        test_cases = [
            {
                'query': 'Tell me about your AI projects',
                'expected_memory': 'semantic',
                'keywords': ['project', 'AI', 'machine learning']
            },
            {
                'query': 'What is your personality like?',
                'expected_memory': 'episodic',
                'keywords': ['friendly', 'enthusiastic']
            }
        ]
        
        results = []
        for case in test_cases:
            try:
                response = chatbot.chat(case['query'], context="", stream=False, save_history=False)
                
                # Check if keywords present
                keywords_found = sum(1 for kw in case['keywords'] if kw.lower() in response.lower())
                
                results.append({
                    'query': case['query'],
                    'expected_memory': case['expected_memory'],
                    'keywords_found': keywords_found,
                    'total_keywords': len(case['keywords']),
                    'success': keywords_found > 0
                })
            except Exception as e:
                results.append({
                    'query': case['query'],
                    'success': False,
                    'error': str(e)
                })
        
        return {
            'test': 'memory_retrieval',
            'cases_tested': len(test_cases),
            'results': results
        }
    
    def check_collection_health(self) -> Dict:
        """Check health of Qdrant collections."""
        client = QdrantClient(path=config.qdrant_local_path, prefer_grpc=False)
        
        health = {}
        for collection in [
            config.semantic_memory_collection,
            config.episodic_memory_collection,
            config.procedural_memory_collection
        ]:
            try:
                count = client.count(collection_name=collection).count
                info = client.get_collection(collection_name=collection)
                
                health[collection] = {
                    'exists': True,
                    'point_count': count,
                    'vector_size': info.config.params.vectors.size,
                    'status': 'healthy' if count > 0 else 'empty'
                }
            except Exception as e:
                health[collection] = {
                    'exists': False,
                    'error': str(e),
                    'status': 'error'
                }
        
        return {
            'test': 'collection_health',
            'collections': health
        }


def main():
    print("TwinSelf Performance Monitor")
    print("=" * 60)
    
    monitor = PerformanceMonitor()
    
    # Check collection health
    print("\nChecking collection health...")
    health = monitor.check_collection_health()
    for coll, status in health['collections'].items():
        if status['exists']:
            print(f"{coll}: {status['point_count']} points ({status['status']})")
        else:
            print(f"{coll}: {status['error']}")
    monitor.log_metric(health)
    
    # Initialize chatbot
    print("\nInitializing chatbot...")
    try:
        chatbot = DigitalTwinChatbot(bot_name="Test Bot")
        print("Chatbot initialized")
    except Exception as e:
        print(f"Failed to initialize: {e}")
        return
    
    # Test response time
    print("\nTesting response time...")
    test_queries = [
        "Hello, who are you?",
        "Tell me about your skills",
        "What projects have you worked on?"
    ]
    
    response_test = monitor.test_response_time(chatbot, test_queries)
    print(f"  Average response time: {response_test['avg_response_time']:.2f}s")
    print(f"  Success rate: {response_test['success_rate']*100:.1f}%")
    monitor.log_metric(response_test)
    
    # Test memory retrieval
    print("\nTesting memory retrieval...")
    memory_test = monitor.test_memory_retrieval(chatbot)
    print(f"  Cases tested: {memory_test['cases_tested']}")
    for result in memory_test['results']:
        if result['success']:
            print(f"{result['query'][:50]}...")
        else:
            print(f"{result['query'][:50]}...")
    monitor.log_metric(memory_test)
    
    print("\n" + "=" * 60)
    print("Performance monitoring complete")
    print(f"Logs saved to: {monitor.log_path}")


if __name__ == "__main__":
    main()
