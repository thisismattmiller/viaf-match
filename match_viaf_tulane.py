# -*- encoding: utf-8 -*-
import time, requests, json, sys, csv
import xml.etree.ElementTree as etree 
 



class viafSearch:




	viafURL = 'http://viaf.org/viaf/search?query=local.personalNames+%3D+{SEARCH}&httpAccept=text/xml'
	sourceFile = 'tulane-no-dupes.csv'
	resultsFile = 'tulane_results.json'
	results = {}
	requestDelay = 0.1



	def __init__(self):


		self.processFile()

		self.saveFile()

		self.stats()




	def requestProcess(self,searchVal):


		

		r = requests.get(self.viafURL.replace('{SEARCH}',searchVal))

		time.sleep(self.requestDelay)

		results = []

		if (r.status_code == 200):


			try:
				root = etree.fromstring(r.text)	
			except:
				print ("Error in parsing the XML", "URL")

			for records in root.findall('{http://www.loc.gov/zing/srw/}records'):
				for record in records:


					aResult = {}
					aResult['birthDate'] = None
					aResult['deathDate'] = None
					aResult['altNames'] = []
					aResult['sources'] = []
					aResult['titles'] = []


					for recordData in record.findall('{http://www.loc.gov/zing/srw/}recordData'):


						for viafCluster in recordData.findall('{http://viaf.org/viaf/terms#}VIAFCluster'):


							for el in viafCluster.findall('{http://viaf.org/viaf/terms#}birthDate'):
								aResult['birthDate'] = el.text

							for el in viafCluster.findall('{http://viaf.org/viaf/terms#}deathDate'):
								aResult['deathDate'] = el.text

							for mainHeadings in viafCluster.findall('{http://viaf.org/viaf/terms#}mainHeadings'):
								for el in mainHeadings.findall('{http://viaf.org/viaf/terms#}data'):
									aResult['altNames'].append((el[0].text))

							for sources in viafCluster.findall('{http://viaf.org/viaf/terms#}sources'):
								for el in sources:
									aResult['sources'].append(el.text)

							for titles in viafCluster.findall('{http://viaf.org/viaf/terms#}titles'):
								for el in titles:
									aResult['titles'] .append(el[0].text)


					results.append(aResult)

			return results						

		else:


			print ("Error in requesting", "URL")

			return []


	def processFile(self):

		counter = 0

		with open(self.sourceFile, 'r') as csvfile:

			#dumps the file into the csv library with some info on how it is formatted
			persons = csv.reader(csvfile, delimiter=',')
			
			for row in persons:
				
				fullName = row[0]
				firstName = row[1]
				lastName = row[2]
				dobYear = row[3]
				dodYear = row[4]


				self.results[fullName]  = {}

				self.results[fullName]['tulane_name'] = fullName
				self.results[fullName]['tulane_first'] = firstName
				self.results[fullName]['tulane_last'] = lastName
				self.results[fullName]['tulane_dob'] = dobYear
				self.results[fullName]['tulane_dod'] = dodYear
				self.results[fullName]['mapping'] = []

				#here is a line of data from tulane


				counter = counter + 1
				print ("On ", counter)

				self.processPerson(fullName)


				#save
				if counter % 25 == 0:
					self.saveFile()


	def processPerson(self,fullName):


		print (self.results[fullName]['tulane_name'])

		searchResult = []


		searchString = self.results[fullName]['tulane_name']

		if (self.results[fullName]['tulane_dob'] != 'NULL'):

			searchString += " " + self.results[fullName]['tulane_dob']

			#search with the DOB one way
			searchResult = self.requestProcess(searchString)

			print ("\t",searchString,"Found:",len(searchResult))

			if (len(searchResult) == 0):

				#try another format that VIAF search engine seems to like sometimes
				searchString = self.results[fullName]['tulane_name'] + "," + self.results[fullName]['tulane_dob']

				print ("\t",searchString,"Found:",len(searchResult))


		#if no luck with that try regular name search
		if (len(searchResult) == 0):

			searchString = self.results[fullName]['tulane_name']
			searchResult = self.requestProcess(searchString)

			print ("\t",searchString,"Found:",len(searchResult))

		quality = "low"

		#lets qualify a little bit
		if(self.results[fullName]['tulane_dob'] != 'NULL' and len(searchResult) == 1):
			quality = 'high'

		if(self.results[fullName]['tulane_dob'] == 'NULL' and len(searchResult) == 1):
			quality = 'medium'

		if(len(searchResult) > 1):
			quality = 'many'

		if(len(searchResult) == 0):
			quality = 'none'

		if(len(searchResult) == 100):
			searchResult = []
			quality = 'manual'




		self.results[fullName]['mapping'] = searchResult
		self.results[fullName]['mapping_quality'] = quality


	def saveFile(self):
		f = open(self.resultsFile, "w")
		f.write(json.dumps(self.results))



	def stats(self):


		matchTypes = {}
		manyMatchCount = {}

		with open(self.resultsFile, 'r') as jsonFile:


			results = json.loads(jsonFile.read())

			for aResult in results:

				x =  results[aResult]

				if x['mapping_quality'] not in matchTypes:
					matchTypes[x['mapping_quality']] = 1
				else:
					matchTypes[x['mapping_quality']] += 1


				if x['mapping_quality'] == 'many':

					if len(x['mapping']) not in manyMatchCount:
						manyMatchCount[len(x['mapping'])] = 1
					else:
						manyMatchCount[len(x['mapping'])] += 1



		print (matchTypes)

		for x in manyMatchCount:
			print (x,"|",manyMatchCount[x])



if __name__ == "__main__":

	v = viafSearch()
