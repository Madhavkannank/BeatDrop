import unittest

class TestTransformations(unittest.TestCase):
    def test_duration_ms_to_seconds(self):
        duration_ms = 210000
        duration_sec = duration_ms // 1000
        self.assertEqual(duration_sec, 210)

    def test_popularity_tier_logic(self):
        def get_popularity_tier(pop):
            if pop >= 75:
                return "HIT"
            elif pop >= 50:
                return "MAINSTREAM"
            else:
                return "NICHE"

        self.assertEqual(get_popularity_tier(90), "HIT")
        self.assertEqual(get_popularity_tier(75), "HIT")
        self.assertEqual(get_popularity_tier(60), "MAINSTREAM")
        self.assertEqual(get_popularity_tier(50), "MAINSTREAM")
        self.assertEqual(get_popularity_tier(40), "NICHE")
        self.assertEqual(get_popularity_tier(0), "NICHE")

    def test_mapreduce_tokens_parsing(self):
        raw_tsv_line = "TRK123456\tBohemian Rhapsody\tQueen\tA Night at the Opera\tRock\t88\t354000\t0\t1975"
        tokens = raw_tsv_line.split("\t")
        self.assertEqual(len(tokens), 9)
        artist = tokens[2]
        popularity = int(tokens[5])
        duration_ms = int(tokens[6])

        self.assertEqual(artist, "Queen")
        self.assertEqual(popularity, 88)
        self.assertEqual(duration_ms, 354000)

if __name__ == "__main__":
    unittest.main()
