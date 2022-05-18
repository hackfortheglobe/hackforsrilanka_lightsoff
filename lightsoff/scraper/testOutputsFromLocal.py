
from scraper import extract_data, validate_extracted_data, save_all_outputs, export_outputs_to_CSV

TARGET_FILE = "./temp/ceb_current.pdf"


if __name__ == "__main__":
    print()
    print("testOutputsFromLocal: Read hardcoded local doc, scrape data and export results in JSON and CSV")
    result = extract_data(TARGET_FILE)
    place_data = result[0]
    schedule_data = result[1]
    last_processed_id = "12345678hardcoded"
    validate_extracted_data(place_data, schedule_data)
    print("Saving outputs as JSON files...")
    save_all_outputs(place_data, schedule_data, last_processed_id)
    print("Saving outputs as CSV files...")
    export_outputs_to_CSV(place_data, schedule_data)
    print("All done.")
