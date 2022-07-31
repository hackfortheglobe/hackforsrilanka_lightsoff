
from lightsoff.models import LastProcessedDocument
from scraper import scrape
import json
import os

if __name__ == "__main__":

    print()
    print("Starting tests: no results will be pushed to DB and outputs will be save in folder.")

    # Get LastProcessedDocument from database
    stored_last_processed = LastProcessedDocument.objects.all().last()
    stored_composite_id = stored_last_processed.last_processed_id

    # Switch from running locally (uncomment next line and comment previous lines and the first import)
    #stored_composite_id = "1Zs6wSUdAVyp1wqVnMnFkzlxDCTaGryL-;;5670"

    COMPOSITE_SEPARATOR = ";;"
    last_pdf_id = stored_composite_id.split(COMPOSITE_SEPARATOR)[0]
    last_proxy_id = stored_composite_id.split(COMPOSITE_SEPARATOR)[1]
    scraperFolder = f"{os.path.dirname(os.path.abspath(__file__))}/"
    outputsFolder = f"{scraperFolder}scraper/outputs/"

    print()
    print("Starting test 'Nothing', passing lastCompositeId, nothing should be scraped...")
    result = scrape(last_pdf_id, last_proxy_id)
    with open(os.path.join(outputsFolder, 'new_scraper_nothing.json'), 'w') as outfile:
        json.dump(result, outfile, indent=4)

    print()
    print("Starting test 'One', passing lastProxyId - 1, only one schedule should be scraped...")
    last_proxy_id_minus_one= str(int(last_proxy_id) - 1)
    result = scrape(last_pdf_id, last_proxy_id_minus_one)
    with open(os.path.join(outputsFolder, 'new_scraper_one.json'), 'w') as outfile:
        json.dump(result, outfile, indent=4)

    print()
    print("Starting test 'All', passing empty doc id, a lot will be scraped...")
    result = scrape("", "")
    with open(os.path.join(outputsFolder, 'new_scraper_all.json'), 'w') as outfile:
        json.dump(result, outfile, indent=4)

    print("Data saved in new_scraper.json")
