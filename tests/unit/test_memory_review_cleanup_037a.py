import unittest

from jarvis.memory.review import build_memory_review


class _Match:
    def __init__(self, record, score=1.0):
        self.record = record
        self.score = score


class _Record:
    def __init__(self):
        self.name = "Kenleigh"
        self.entity_type = "person"
        self.attributes = {"relationship": "fiance", "attribute_backfill": "fiancee"}
        self.summary = "Kenleigh is your fiance; Kenleigh is your fiancée."
        self.relationships = [
            {"source": "attribute_backfill", "target": "user", "type": "fiancee"},
            {"source": "Kenleigh", "target": "user", "type": "fiance"},
        ]
        self.aliases = ["Ken Lee"]
        self.importance = 4


class _EntityMemory:
    def search(self, subject, limit=12):
        return [_Match(_Record())]


class MemoryReviewCleanup037aTests(unittest.TestCase):
    def test_review_hides_internal_labels_and_dedupes_relationships(self):
        review = build_memory_review("Kenley", entity_memory=_EntityMemory())
        texts = [item.text for item in review.items]
        joined = "\n".join(texts).lower()
        self.assertNotIn("attribute_backfill", joined)
        self.assertNotIn("attribute backfill", joined)
        self.assertIn("Kenleigh is your fiancée.", texts)
        relationship_count = sum(1 for text in texts if text == "Kenleigh is your fiancée.")
        self.assertEqual(relationship_count, 1)


if __name__ == "__main__":
    unittest.main()
