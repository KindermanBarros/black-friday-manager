import unittest
from collect import canonical, classify, number
from publish import append, fallback

class Contract(unittest.TestCase):
    def test_url(self):
        self.assertEqual(canonical("https://WWW.amazon.com.br/dp/A/?utm_source=x&b=2&a=1#x"), "https://amazon.com.br/dp/A?a=1&b=2")
    def test_snapshot_retry(self):
        run = fallback("2026-11-27T04:30:00-04:00", "test")
        d = {"runs": [{"at": "old", "offers": []}]}
        append(d, run)
        append(d, run)
        self.assertEqual(len(d["runs"]), 2)
        self.assertEqual(d["runs"][0]["at"], "old")
    def test_switch(self):
        o = {"price": 3000}
        self.assertEqual(classify("switch", "Console Nintendo Switch 2 com Mario Kart World", "", o)["games"], ["Mario Kart World"])
        self.assertIsNone(classify("switch", "Capa Nintendo Switch 2", "", o))
        self.assertIsNone(classify("switch", "Console Nintendo Switch 2 bundle", "", o))
    def test_pc(self):
        o = {"price": 5800}
        self.assertEqual(classify("pc", "PC Gamer Ryzen 7 5700X RTX 5060 16GB RAM", "", o)["ramGB"], 16)
        self.assertIsNone(classify("pc", "Notebook i7 12700H RTX 5060 16GB RAM", "", o))
    def test_phone(self):
        self.assertIsNone(classify("phone", "Samsung Galaxy S25 Ultra", "", {"price": 4000}))
        self.assertEqual(classify("phone", "Samsung Galaxy S25 Ultra", "", {"price": 3900})["brand"], "Samsung")
    def test_price(self):
        self.assertEqual(number("R$ 3.299,90"), 3299.90)

if __name__ == "__main__":
    unittest.main()
