import unittest
from io import BytesIO
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

from data_utils import demo_data, to_excel, validate_data


class DataTests(unittest.TestCase):
    def test_excel_roundtrip(self):
        data = demo_data(6)
        loaded = validate_data(pd.read_excel(BytesIO(to_excel(data))))
        self.assertEqual(len(loaded), 73)
        pd.testing.assert_frame_equal(data, loaded, check_exact=False, atol=1e-10)

    def test_reject_bad_measurements(self):
        for column, value in [("methanol", 101), ("flow", -1), ("pressure", float("inf")), ("timestamp", "bad")]:
            with self.subTest(column=column):
                data = demo_data(6)
                data[column] = value
                with self.assertRaises(ValueError):
                    validate_data(data)

    def test_demo_interface(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run(timeout=30)
        self.assertFalse(app.exception)
        self.assertEqual(len(app.metric), 4)
        self.assertEqual(len(app.get("plotly_chart")), 4)
        app.sidebar.radio[0].set_value("Excel").run()
        self.assertFalse(app.exception)
        self.assertIn("Загрузите Excel", app.info[0].value)


if __name__ == "__main__":
    unittest.main()
