import boto3
import json
import sys
import requests
import time

#TODO: Parameterize all of these variables
arguments = sys.argv
print("Arguments: ", arguments)
ip = arguments[1]
print("Ip: ", ip)
confidenceThreshold = float(arguments[2])
print("Confidence Threshold: ", confidenceThreshold)
keywords = arguments[3:]
print("Keywords:", keywords)

localFilePathPrefix = "/Users/ronding/Desktop/canon_photos/"

client = boto3.client("rekognition")

def initApi():
	url = "http://{}:8080/ccapi/".format(ip)
	getRequest(url, None)

#shutter button manual press
#shutter button manual release synchronous
def takePhoto():
	print("takePhoto called")
	url = "http://{}:8080/ccapi/ver100/shooting/control/shutterbutton/manual".format(ip)
	shutterParams = {
		"action": "full_press",
		"af": True
	}
	r = postRequest(url, json.dumps(shutterParams))
	shutterParams["action"] = "release"
	postRequest(url, json.dumps(shutterParams))

#Get the filePath of the downloaded file
def downloadLastPhoto():
	#Get list of photos
	print("downloadLastPhoto called")
	url = "http://{}:8080/ccapi/ver100/contents/sd/100CANON".format(ip)
	photoUrlList = getRequest(url, None)["url"]
	lastImageUrl = photoUrlList[-1] #Verify the newest photo is at the front or back of the list
	return downloadPhoto(lastImageUrl)

#pull photo from sd card
def downloadPhoto(url):
	print("downloadPhoto called with url: ", url)
	photoMetaData = {}
	photoMetaData["imageUrl"] = url
	r = getImageRequest(url, None)
	filePath = localFilePathPrefix + url.split("/")[-1]
	print("Photo saved at filePath: ", filePath)
	with open(filePath, "wb") as f:
		f.write(r.content)
	photoMetaData["filePath"] = filePath
	return photoMetaData

#delete photo from sd card
def deletePhoto(url):
	print("deletePhoto called with url: ", url)
	return deleteRequest(url)

#get request
def getRequest(requestUrl, requestParams):
	print("getRequest called with requestUrl: ", requestUrl)
	return requests.get(url = requestUrl, params = requestParams).json()

#get image
def getImageRequest(requestUrl, requestParams):
	print("getImageRequest called with requestUrl: ", requestUrl)
	return requests.get(url = requestUrl, params = requestParams)

# post request
def postRequest(requestUrl, requestData):
	print("postRequest called with requestUrl: ", requestUrl)
	return requests.post(url = requestUrl, data = requestData, headers = {"Content-Type": "application/json"}).json()

# delete request
def deleteRequest(requestUrl):
	print("deleteRequest called with requestUrl: ", requestUrl)
	return requests.delete(url = requestUrl).json()

#AWS request to Rekognition
#Return a list of strings 
def getLabelsFromRekognition(filePath):
	print("getLabelsFromRekognition called with filePath: ", filePath)
	labelsAboveConfidence = []
	with open(filePath, 'rb') as image:
		response = client.detect_labels(Image = {"Bytes": image.read()})
	for label in response['Labels']:
		if label['Confidence'] > confidenceThreshold:
			labelsAboveConfidence.append(label['Name'])
	return labelsAboveConfidence

def injectDelay(duration):
	print("injectDelay called with duration: ", duration)
	time.sleep(duration)

def convertLabelsToLowerCase(labels):
	print("convertLabelsToLowerCase called with labels: ", labels)
	for i in range(len(labels)):
		labels[i] = labels[i].lower()
	return labels

initApi()

while(True):
	takePhoto()
	injectDelay(1.5)
	photoMetaData = downloadLastPhoto()
	labels = convertLabelsToLowerCase(getLabelsFromRekognition(photoMetaData["filePath"]))
	save = False
	for keyword in keywords:
		if keyword in labels:
			save = True
			break

	if (save == False):
		deletePhoto(photoMetaData["imageUrl"])
	print("YOU CAN SAFELY TERMINATE NOW")
	injectDelay(1)
	print("YOU CAN NOT SAFELY TERMINATE ANYMORE")


