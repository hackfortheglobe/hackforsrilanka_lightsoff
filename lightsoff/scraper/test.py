
from scraper import scrape

if __name__ == "__main__":
    
    print("Starting test, passing current doc id, should be skipped...")
    scrape("1DN_Oxe3X6q1W02wgNzMT88HXX-vk3xFJ")

    print()
    print("Now passing empty doc id, should be processed...")
    scrape("")