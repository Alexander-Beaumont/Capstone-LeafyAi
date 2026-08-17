from django.test import TestCase
from django.utils import timezone
from ai_agent.models import AIDecision
from telemetry.models import PlantBatch

class AIDecisionModelTests(TestCase):
    
    def setUp(self):
        """
        setUp runs automatically before every test. 
        We use it to create the prerequisite database objects.
        """
        # Create a mock PlantBatch with the required planting_date
        self.test_batch = PlantBatch.objects.create(
            planting_date=timezone.now().date()
        )

    def test_aidecision_links_to_plantbatch(self):
        """Test that a new AIDecision correctly links to a PlantBatch."""
        
        # 1. Create a new AIDecision and assign our mock batch as the foreign key
        decision = AIDecision.objects.create(
            plant_batch=self.test_batch,
            decision_type="Nutrient Adjustment",
            recommendation="Increase EC to 1500 uS/cm",
            explanation="EC is dropping below the target threshold for the vegetative stage.",
            confidence_score=0.92
        )

        # 2. Fetch the newly created decision from the database
        saved_decision = AIDecision.objects.get(id=decision.id)

        # 3. Assert that the linked PlantBatch is exactly the one we created
        self.assertEqual(saved_decision.plant_batch, self.test_batch)
        self.assertEqual(saved_decision.plant_batch.id, self.test_batch.id)