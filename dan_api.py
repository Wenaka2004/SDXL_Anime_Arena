import requests

api_key = "NEdaaKB66AQMEivXx1YXpJ81"

def search_images(tags, limit=10):
    url = 'https://danbooru.donmai.us/posts.json'
    params = {
        'tags': tags,
        'api_key': "NEdaaKB66AQMEivXx1YXpJ81",
        'limit': limit,
        'login':'Wenaka',
        'tag_count_character': 1
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        results=[]
        for post in data:
            #如果large_file_url不存在，使用file_url
            if 'large_file_url' in post:
                results.append(post['large_file_url'])
            else:
                results.append(post['file_url'])
        return results

        
    except requests.exceptions.RequestException as e:
        print(f"请求出错: {e}")
        return None

# 使用示例
if __name__ == '__main__':
    tags = 'kamisato_ayaka'
    username='Wenaka'
    results = search_images(tags)
    #show the image from the url
    print(results)
