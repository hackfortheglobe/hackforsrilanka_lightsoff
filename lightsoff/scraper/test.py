
from scraper import scrape
import json
import os

if __name__ == "__main__":
    
    print()

    print("Starting test, passing empty doc id, should be always processed...")
    #result = scrape("", "")

    #print("Starting test, lastCompositeId, should be skipped...")
    result = scrape("1Zs6wSUdAVyp1wqVnMnFkzlxDCTaGryL-", "5399")

    with open(os.path.join('outputs', 'new_scraper.json'), 'w') as outfile:
        json.dump(result, outfile, indent=4)
    print("Data saved in new_scraper.json")
