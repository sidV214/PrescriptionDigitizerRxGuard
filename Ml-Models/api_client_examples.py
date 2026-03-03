"""
Example client code for using the Prescription Processing API
Shows how to integrate with the FastAPI endpoints
"""

import requests
import json
import sys
from typing import Dict, List
from pathlib import Path

BASE_URL = "http://localhost:8000"


class PrescriptionAPIClient:
    """Client for Prescription Processing API"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self) -> Dict:
        """Check if API is running"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_status(self) -> Dict:
        """Get system status"""
        response = self.session.get(f"{self.base_url}/status")
        return response.json()
    
    def process_text(self, prescription_text: str, enable_ocr: bool = False) -> Dict:
        """Process prescription from text"""
        payload = {
            "prescription_text": prescription_text,
            "enable_ocr": enable_ocr
        }
        response = self.session.post(
            f"{self.base_url}/process/text",
            json=payload
        )
        return response.json()
    
    def process_image(self, image_path: str) -> Dict:
        """Process prescription from image file"""
        with open(image_path, "rb") as f:
            files = {"file": f}
            response = self.session.post(
                f"{self.base_url}/process/image",
                files=files
            )
        return response.json()
    
    def process_batch(self, prescriptions: List[str]) -> Dict:
        """Process multiple prescriptions"""
        payload = {"prescriptions": prescriptions}
        response = self.session.post(
            f"{self.base_url}/process/batch",
            json=payload
        )
        return response.json()


# ===== Example 1: Health Check and Status =====
def example_1_health_check():
    """Example 1: Check if API is healthy"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Health Check and Status")
    print("="*70)
    
    client = PrescriptionAPIClient()
    
    # Health check
    print("\n✓ Checking health...")
    health = client.health_check()
    print(f"  Status: {health.get('status')}")
    print(f"  Message: {health.get('message')}")
    
    # Get status
    print("\n✓ Getting system status...")
    status = client.get_status()
    print(f"  Status: {status.get('status')}")
    print(f"  Version: {status.get('version')}")
    print(f"  Models available:")
    for model, available in status.get('models_available', {}).items():
        symbol = "✓" if available else "✗"
        print(f"    {symbol} {model}")


# ===== Example 2: Process Single Text Prescription =====
def example_2_process_text():
    """Example 2: Process prescription from text"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Process Text Prescription")
    print("="*70)
    
    client = PrescriptionAPIClient()
    
    prescription_text = """
    Patient: John Doe
    
    Prescriptions:
    1. Aspirin 500mg - take twice daily for 7 days
    2. Metformin 1000mg - once daily for 30 days
    3. Ibuprofen 400mg - every 6 hours as needed
    """
    
    print(f"\n📝 Processing prescription:")
    print(f"  {prescription_text[:100]}...")
    
    result = client.process_text(prescription_text)
    
    print(f"\n✓ Processing completed: {result.get('status')}")
    print(f"  Medicines found: {result.get('total_medicines')}")
    print(f"  Interactions found: {result.get('total_interactions')}")
    print(f"  Processing time: {result.get('processing_time_ms'):.2f}ms")
    
    # Display medicines
    print(f"\n📋 Medicines:")
    for med in result.get('medicines', []):
        print(f"  • {med['name']} ({med.get('dosage', 'N/A')})")
        print(f"    - Frequency: {med.get('frequency', 'N/A')}")
        print(f"    - Duration: {med.get('duration', 'N/A')}")
        print(f"    - Confidence: {med.get('confidence', 0):.2%}")
    
    # Display interactions
    if result.get('interactions'):
        print(f"\n⚠️  Drug Interactions:")
        for interaction in result.get('interactions', []):
            print(f"  • {interaction['drug1']} + {interaction['drug2']}")
            print(f"    - Severity: {interaction.get('severity', 'N/A')}")
            print(f"    - Risk Score: {interaction.get('risk_score', 0):.2%}")
            print(f"    - Description: {interaction.get('description', 'N/A')}")


# ===== Example 3: Batch Processing =====
def example_3_batch_processing():
    """Example 3: Process multiple prescriptions"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Batch Processing")
    print("="*70)
    
    client = PrescriptionAPIClient()
    
    prescriptions = [
        "Take Aspirin 500mg twice daily for 7 days",
        "Metformin 1000mg once daily for 30 days",
        "Lisinopril 10mg once daily",
        "Ibuprofen 400mg as needed for pain"
    ]
    
    print(f"\n📝 Processing {len(prescriptions)} prescriptions...")
    
    result = client.process_batch(prescriptions)
    
    print(f"\n✓ Batch processing completed: {result.get('status')}")
    print(f"  Total processed: {result.get('total_processed')}")
    
    print(f"\n📊 Results:")
    for item in result.get('results', []):
        status = "✓" if item['status'] == "success" else "✗"
        print(f"  {status} Prescription {item['index'] + 1}")
        if item['status'] == "success":
            print(f"     Medicines: {item.get('medicines_count', 0)}")
            print(f"     Interactions: {item.get('interactions_count', 0)}")
        else:
            print(f"     Error: {item.get('error', 'Unknown error')}")


# ===== Example 4: Process Image =====
def example_4_process_image():
    """Example 4: Process prescription image"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Process Image")
    print("="*70)
    
    client = PrescriptionAPIClient()
    
    # Check if sample image exists
    image_path = "sample_prescription.jpg"
    
    if not Path(image_path).exists():
        print(f"\n❌ Sample image not found: {image_path}")
        print("   To test image processing:")
        print("   1. Create a prescription image")
        print("   2. Save it as 'sample_prescription.jpg'")
        print("   3. Run this example again")
        return
    
    print(f"\n🖼️  Processing image: {image_path}")
    
    result = client.process_image(image_path)
    
    print(f"\n✓ Image processing completed: {result.get('status')}")
    print(f"  Medicines found: {result.get('total_medicines')}")
    print(f"  Processing time: {result.get('processing_time_ms'):.2f}ms")
    
    # Display medicines
    if result.get('medicines'):
        print(f"\n📋 Extracted Medicines:")
        for med in result.get('medicines', []):
            print(f"  • {med['name']} ({med.get('dosage', 'N/A')})")


# ===== Example 5: Error Handling =====
def example_5_error_handling():
    """Example 5: Handle errors gracefully"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Error Handling")
    print("="*70)
    
    client = PrescriptionAPIClient()
    
    # Test 1: Empty prescription
    print("\n🧪 Test 1: Empty prescription")
    try:
        result = client.process_text("")
        if "detail" in result:
            print(f"  ✓ Error handled: {result['detail']}")
    except Exception as e:
        print(f"  ✓ Exception caught: {str(e)}")
    
    # Test 2: Check API availability
    print("\n🧪 Test 2: Check API availability")
    health = client.health_check()
    if health.get('status') == 'healthy':
        print(f"  ✓ API is available")
    else:
        print(f"  ✗ API is not available - ensure server is running")
        print(f"    Run: python run_api.py")


# ===== Example 6: Advanced Usage =====
def example_6_advanced_usage():
    """Example 6: Advanced integration patterns"""
    print("\n" + "="*70)
    print("EXAMPLE 6: Advanced Usage")
    print("="*70)
    
    client = PrescriptionAPIClient()
    
    # Process and analyze results
    print("\n📊 Processing prescription with detailed analysis...")
    
    prescription = """
    Dr. Smith
    Date: 2024-01-15
    
    Patient: John Doe
    Age: 45
    
    Prescriptions:
    1. Aspirin 500mg - twice daily for 7 days (pain relief)
    2. Metformin 1000mg - once daily for 30 days (diabetes)
    3. Ibuprofen 400mg - every 6 hours as needed (inflammation)
    """
    
    result = client.process_text(prescription)
    
    # Severity analysis
    print("\n🔍 Interaction Severity Analysis:")
    high_risk = sum(1 for i in result.get('interactions', []) if i.get('severity') == 'high')
    moderate_risk = sum(1 for i in result.get('interactions', []) if i.get('severity') == 'moderate')
    low_risk = sum(1 for i in result.get('interactions', []) if i.get('severity') == 'low')
    
    print(f"  🔴 High Risk: {high_risk}")
    print(f"  🟠 Moderate Risk: {moderate_risk}")
    print(f"  🟡 Low Risk: {low_risk}")
    
    # Confidence scores
    print("\n📈 Confidence Scores:")
    for med in result.get('medicines', []):
        confidence_pct = med.get('confidence', 0) * 100
        bar = "█" * int(confidence_pct / 5) + "░" * (20 - int(confidence_pct / 5))
        print(f"  {med['name']}: [{bar}] {confidence_pct:.1f}%")
    
    # Export results
    print("\n💾 Export data:")
    export_data = {
        "timestamp": None,
        "prescription_text": prescription[:50] + "...",
        "medicines_count": result.get('total_medicines'),
        "interactions_count": result.get('total_interactions'),
        "processing_time_ms": result.get('processing_time_ms')
    }
    print(f"  {json.dumps(export_data, indent=2)}")


def main():
    """Run all examples"""
    print("\n" + "="*70)
    print("PRESCRIPTION PROCESSING API - Client Examples")
    print("="*70)
    print("\nMake sure the API is running:")
    print("  python run_api.py")
    print("\nOr visit the interactive docs:")
    print("  http://localhost:8000/api/docs")
    
    try:
        # Run examples
        example_1_health_check()
        example_2_process_text()
        example_3_batch_processing()
        example_4_process_image()
        example_5_error_handling()
        example_6_advanced_usage()
        
        print("\n" + "="*70)
        print("✓ All examples completed!")
        print("="*70)
        print("\n📚 Next steps:")
        print("  1. Visit: http://localhost:8000/api/docs")
        print("  2. Try different prescriptions")
        print("  3. Integrate with your application")
        print("  4. Check API_DOCUMENTATION.md for more details")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {str(e)}")
        print("\nMake sure the API server is running:")
        print("  python run_api.py")
        sys.exit(1)


if __name__ == "__main__":
    main()
