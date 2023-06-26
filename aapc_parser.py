import requests
from bs4 import BeautifulSoup

#cloudflare encrypts emails; this function decrypts them
def cf_decode_email(encodedString):
    r = int(encodedString[:2],16)
    email = ''.join([chr(int(encodedString[i:i+2], 16) ^ r) for i in range(2, len(encodedString), 2)])
    return email

first_srp_url = 'https://theaapc.org/find-a-consultant/?consultant_name=&party_affiliation=&international=&award_winners=&filter-submit='
srp_urls = [first_srp_url]
member_page_urls = []

#get all search results pages
for i in range(2, 33):
    srp_urls.append(first_srp_url + f'& pg={i}')

#get all member page urls (20 per page)
for url in srp_urls:
    page = requests.get(url, headers={'user-agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(page.content, 'html.parser')
    results = soup.find(id='av_section_3')
    consultants = results.find_all('div', class_='consultant_result_div')
    consultant_link_elements = results.find_all('div', class_='col-12')
    python_job_elements = [link_element.child for link_element in consultant_link_elements]
    for link_element in consultant_link_elements:
        link_url = link_element.find('a')['href']
        member_page_urls.append(link_url) 


f = open(os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'Outputs', 'aapc-scrape.csv')), 'a')

for url in member_page_urls:
    page = requests.get(url, headers={'user-agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(page.content, 'html.parser')
    record = {'First Name': '', 'Last Name': '', 'Company Name': '', 'Party Affiliation': '', 'Street Address 1': '', 'Street Address 2': '', 'City': '', 'State': '', 'Zip': '', 'E-mail': '', 'Business Phone': '', 'Mobile Phone': '', 'Areas of Expertise': ''}
    full_name = soup.find('h2', class_='av-special-heading-tag').text.replace(',', '').strip()
    record['First Name'] = full_name[:full_name.index(' ')] if ' ' in full_name else ''
    record['Last Name'] = full_name[full_name.index(' ')+1:] if ' ' in full_name else ''
    data_table = soup.find('table', class_='single-org-data')
    data_rows = data_table.find_all('tr')
    for row in data_rows:
        key = row.find('td').text
        # print(f'key: {key}')
        value_el = row.find('td').next_sibling.next_sibling
        if key == 'E-mail':
            record[key] = cf_decode_email(value_el.find('a').find('span')['data-cfemail'])
            # print(f'value: {record[key]}')
        elif key == 'Address':
            str_buffer = ' '*48
            street_address = value_el.contents[0].lstrip().rstrip()
            street_address_arr = street_address.split(str_buffer) if str_buffer in street_address else [street_address]
            city_state_zip = value_el.contents[2].lstrip().rstrip()
            city_state_zip_arr = city_state_zip.split(str_buffer) if str_buffer in city_state_zip else [city_state_zip]
            record['Street Address 1'] = street_address_arr[0]
            record['Street Address 2'] = street_address_arr[1] if len(street_address_arr) > 1 else ''
            record['City'] = city_state_zip_arr[0][:city_state_zip_arr[0].index(',')].strip()
            record['State'] = city_state_zip_arr[1][:city_state_zip_arr[1].index('-')].strip()
            record['Zip'] = city_state_zip_arr[2]
        else:
            record[key] = value_el.text.strip().replace(',','|')
    f.write(f"\n{record['First Name']},{record['Last Name']},{record['Company Name']},{record['Party Affiliation']},{record['Street Address 1']},{record['Street Address 2']},{record['City']},{record['State']},{record['Zip']},,{record['E-mail']},,,{record['Business Phone']},{record['Mobile Phone']},{record['Areas of Expertise']}")
