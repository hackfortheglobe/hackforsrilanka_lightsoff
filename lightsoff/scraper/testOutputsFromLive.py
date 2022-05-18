
from scraper import scrape, validate_extracted_data, save_all_outputs, export_outputs_to_CSV

if __name__ == "__main__":
    print()
    print("testOutputsFromLive: Get live doc, scrape data and export results in JSON and CSV")
    result = scrape("")
    place_data = result[0]
    schedule_data = result[1]
    last_processed_id = result[2]
    validate_extracted_data(place_data, schedule_data)
    print("Saving outputs as JSON files...")
    save_all_outputs(place_data, schedule_data, last_processed_id)
    print("Saving outputs as CSV files...")
    export_outputs_to_CSV(place_data, schedule_data)
    print("All done.")
