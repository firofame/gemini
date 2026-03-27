#!/usr/bin/env python3

from camoufox.sync_api import Camoufox
import json

def authenticate():
    print('Launching Camoufox for Google authentication...\n')
    
    with Camoufox(headless=False, geoip=True) as browser:
        page = browser.new_page()
        page.goto('https://docs.google.com/document/u/0/')
        
        print('Please sign in to your Google account in the browser window.')
        input('Press Enter here after you have successfully signed in...')
        
        # Get the context from the page
        storage = page.context.storage_state()
        with open('auth.json', 'w') as f:
            json.dump(storage, f, indent=2)
    
    print('\n✅ Authentication saved to auth.json')
    print('You can now run: node tts.js input.txt')

if __name__ == '__main__':
    try:
        authenticate()
    except Exception as e:
        print(f'Authentication failed: {e}')
        exit(1)