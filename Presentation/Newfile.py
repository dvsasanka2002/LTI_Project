import numpy as np
import pandas as pd
import json
import csv
from lxml import etree
from xml.etree import ElementTree as et 
from jsonpath_ng import jsonpath,parse
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
logical_key_csv_file = 'TestCSV.csv'
json_input_file = "Broker_Application_XML.json"
xml_input_file = 'ACORD_XML_For_SubmittionToCarrier.xml'
file = 'input.json'
file1 = 'file.xml'


model = SentenceTransformer('multi-qa-mpnet-base-cos-v1')
df = pd.read_csv(logical_key_csv_file)
Logical_Key = df['Field_Name'].tolist()
#Cosine Similarity
def find_similar(vector_representation, all_representations, k=1):
    similarity_matrix = cosine_similarity(vector_representation, all_representations)
    similarities = similarity_matrix[0]
    if k == 1:
        val = [np.argmax(similarities)]
        return [np.argmax(similarities)]
    elif k is not None:
        return np.flip(similarities.argsort()[-k:][::1])

embeddings_distilbert = model.encode(Logical_Key)

#Logical Key through Pre-Trained Model
def get_logical_key(physical_key) :
    search_string = physical_key
    search_vect = model.encode([search_string])
    k = 1
    distil_bert_similar_indexes = find_similar(search_vect,embeddings_distilbert,k) 
    output_data = []
    for index in distil_bert_similar_indexes :
        output_data.append(Logical_Key[index])
    return output_data        
mylist = []
def getKeys(obj, parent="obj") :
    global mylist
    for i in obj.keys():
        mylist.append(parent+"/"+i)
        try:
            getKeys(obj[i], parent+"/"+i)
        except AttributeError:
            pass
with open(json_input_file, "r") as f:
  data = json.load(f)
getKeys(data)
del mylist[0]
#JSON paths in mylist

#Custom Logic for the Logical Key
with open('synonyms.txt') as f:
    lines = f.readlines()
rows,cols = (len(lines),2)
val = [[0]*cols]*rows
arr = [[0]]*rows
pair = [[0]]*rows
for i in range(len(lines)):
    val[i] = lines[i].split('=')
    val[i][1] = val[i][1].replace('[',"")
    val[i][1] = val[i][1].replace(']\n',"")
    arr[i] = val[i][1].split(',')
    pair[i] = (val[i][0],arr[i])


json_list = mylist

def format_xml_path(xml_path):
    arr = str(xml_path).split('/')
    if(arr[-1] == 'CoverageCd'):
        xml_path = xml_path.replace('CoverageCd','Limit/FormatCurrencyAmt/Amt')
    elif(arr[-1] == 'DeductibleAppliesToCd'):
        xml_path = xml_path.replace('DeductibleAppliesToCd','FormatInteger')
    return xml_path


xml_list = []
with open(xml_input_file, 'r') as f:
    root = etree.parse(f)
    for e in root.iter():
        path = root.getelementpath(e)
        #print(path)
        xml_list.append(path)
del xml_list[0]

#xml_list with all xml paths

#Returns the JSON value stored at the end of the path
def json_value(filename,path) :
    with open(filename,'r') as json_file:
        data = json.load(json_file)
    path = path.replace('/','"."')
    path = path + '"'
    path = path.replace('obj".','')
    jsonpath_expression = parse(path)
    for match in jsonpath_expression.find(data):
        return (match.value)

#Returns the XML value stored at the end of the path
def xml_value(filename,path):
    tree = et.parse(filename)
    root = tree.getroot()
    val = root.find(path).text
    return val
    
def getXML_Json_Matching(filename,path,depth,file_type):
    arr2 = str(path).split('/')
    if(depth <= len(arr2)):
        key = arr2[len(arr2) - depth]
        for j in range(len(lines)):
            for k in range(len(pair[j][1])):
                if(str(key) == str(pair[j][1][k])):
                    return pair[j][0]
                elif((file_type == True) and (xml_value(filename,path) != None) and (str(pair[j][1][k]) == str(xml_value(filename,path)))):
                    return pair[j][0]
                elif((file_type == False) and (json_value(filename,path) != None) and (str(pair[j][1][k]) == str(json_value(filename,path)))):
                    return pair[j][0]
        return "0"    
    else:
        val = str(get_logical_key(arr2[-1]))
        return val   


def getXml_Json_Match(filename,path,depth,key_val_pair,file_type):
    if(getXML_Json_Matching(filename,path,depth,file_type) != "0"):
        key_val_pair.append((path,getXML_Json_Matching(filename,path,depth,file_type)))
        return

    elif(getXML_Json_Matching(filename,path,depth,file_type) == "0"):
        getXml_Json_Match(filename,path,depth+1,key_val_pair,file_type)

key_val_pair_xml = []
depth = 1
for i in range(len(xml_list)):
    getXml_Json_Match(xml_input_file,xml_list[i],depth,key_val_pair_xml,True)

key_val_pair_json = []
depth = 1
for i in range(len(json_list)):
    getXml_Json_Match(json_input_file,json_list[i],depth,key_val_pair_json,False)
        

final_res = []
excel_res_store = []
json_matched_list = []
for a,b in key_val_pair_json:
    for c,d in key_val_pair_xml:
        if(b == d):
            final_res.append((a,c))
            excel_res_store.append((a,b,format_xml_path(c)))
            json_matched_list.append(a)

file = open('output.csv', 'w+', newline ='')

with file:   
    write = csv.writer(file)
    write.writerows(excel_res_store)
for a,b in final_res:
    print(a," : ",format_xml_path(b))            
def get_matched_xml_path(path):
    for a,b in final_res:
        if(path == a):
            return b
def modify_value(value,path,filename) :
    value = str(value)
    tree = et.parse(filename)
    tree.find(path).text = str(value)
    tree.write(filename)


for i in range(len(json_matched_list)) :
    val = json_value(file,json_matched_list[i])
    xml_path = get_matched_xml_path(json_matched_list[i])
    modify_value(val,format_xml_path(xml_path),file1)
            


    

    



           
        
                
                








