import pprint
import requests

pme_list = [1000,1500]

url = "https://prod-89.westeurope.logic.azure.com/workflows/5414fc98231a4e08a9327a64d1ee7ddb/triggers/manual/paths/invoke/1000,1500/2023-01-31%2023:00:00/2023-02-01%2000:00:00?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=IFGbPP6TDH_bOENbb0A6t_b2bn2_HKXrNJv4z4FftCQ"
headers = {"auth-key": "GR4Hrr8sJAQgyGM8j8v2"}

response = requests.get(url=url, headers=headers)

pprint.pprint(response.text)