"""
Allow sync with Guacamole using their undocumented HTTP REST API.
"""
import sys
import logging
import pprint
import urllib.parse
import requests

logging.basicConfig(level=logging.DEBUG,filename='sync.log')
log = logging.getLogger(__name__)

class Guac():
	"""interface with Guacamole API
	tested against Guacamole v1.3.0
	docs: https://github.com/ridvanaltun/guacamole-rest-api-documentation/
	and: https://github.com/apache/guacamole-client/tree/master/guacamole/src/main/webapp/app/rest
	and: Firefox developer mode from a web session as admin.
	and: https://github.com/necouchman/guacamole-python/blob/master/guacamole-cli.py

	Note: sending the token as a GET param is a security issue, as all params are leaked to anyone paying attention.
	it's being fixed here: https://issues.apache.org/jira/browse/GUACAMOLE-956
	"""
	def __init__(self,url=None):
		"""init url = baseURL to reach main guacamole.  '/' @ end is required for urljoin() to work properly.
		for us, via consul: https://prod.guac.service.consul:8080/guacamole/
		"""
		if not url:
			url = 'https://prod.guac.service.consul:8080/guacamole/'
		self.url = url
		self.token = None
		self.headers = {'Accept': 'application/json'}
	def urljoin(self,base, url, allow_fragments=True):
		"""join url's"""
		return urllib.parse.urljoin(base,url,allow_fragments)
	def urlescape(self,url):
		return urllib.parse.quote_plus(url)
	def addUser(self, data):
		"""add a user
		data = {
			"username":"testuser",
			"password":"testuser",
			"attributes":{
				"disabled":"",
				"expired":"",
				"access-window-start":"",
				"access-window-end":"",
				"valid-from":"",
				"valid-until":"",
				"timezone":None,
				"guac-full-name":"Test User",
				"guac-email-address":"testuser@example.com",
				"guac-organizational-role":"190012"
				}
		}
		returns most of the user data back to you:
			{
			"username":"testuser",
			"password":"testuser",
			"attributes":{
				"guac-email-address":"testuser@example.com",
				"guac-organizational-role":"190012",
				"guac-full-name":"Test User",
				"expired":"",
				"access-window-start":"",
				"access-window-end":"",
				"disabled":"",
				"valid-until":"",
				"valid-from":""
				}
			}
		"""
		url = self.urljoin(self.url,'api/session/data/{0}/users'.format(self.dataSource))
		r = requests.post(url,headers=self.headers,params={'token':self.token},json=data)
		return r.json()

	def listConnections(self):
		"""list all connections.
		requires 'Administer system:' permissions. without these, will always return an empty {}.
		returns a dictionary of connections by connection ID.
		i.e.
		r['44'] is connection identifier #44 (so you want d.keys() to get a list of the connections)
		r['44'] will return something like:
		 {'name': 'guacuserprod-cperez2_yumaunion', 'identifier': '44', 'parentIdentifier': 'ROOT', 'protocol': 'rdp', 'attributes': {'guacd-encryption': None, 'failover-only': None, 'weight': None, 'max-connections': None, 'guacd-hostname': None, 'guacd-port': None, 'max-connections-per-user': None}, 'activeConnections': 0}
		"""
		if not self.token:
			raise Exception("Unauthenticated, use auth(user,pass) first.")
		url = self.urljoin(self.url,'api/session/data/{0}/connections'.format(self.dataSource))
		log.debug("guac.listConnections calling: %s" % url)
		r = requests.get(url,headers=self.headers,params={'token':self.token})
		return r.json()
	def listActiveConnections(self):
		"""list all connections.
		requires 'Administer system:' permissions. without these, will always return an empty {}.
		returns a dictionary of connections by connection ID.
		i.e.
		r['44'] is connection identifier #44 (so you want d.keys() to get a list of the connections)
		r['44'] will return something like:
		 {'name': 'guacuserprod-cperez2_yumaunion', 'identifier': '44', 'parentIdentifier': 'ROOT', 'protocol': 'rdp', 'attributes': {'guacd-encryption': None, 'failover-only': None, 'weight': None, 'max-connections': None, 'guacd-hostname': None, 'guacd-port': None, 'max-connections-per-user': None}, 'activeConnections': 0}
		"""
		if not self.token:
			raise Exception("Unauthenticated, use auth(user,pass) first.")
		url = self.urljoin(self.url,'api/session/data/{0}/activeConnections'.format(self.dataSource))
		log.debug("guac.listActiveConnections calling: %s" % url)
		r = requests.get(url,headers=self.headers,params={'token':self.token})
		return r.json()

	def connectionDetails(self,connectionIdentifier):
		"""get details about a particular connection
		connectionIdentifier is an integer, returned from listConnections.keys() or listConnections['id']['identifier']
		>>> r = requests.get('http://prod.guac.service.consul:8080/guacamole/api/session/data/postgresql/connections/44',headers=head,params={'token':token})
		>>> r.json()
		{'name': 'guacuserprod-testuser', 'identifier': '44', 'parentIdentifier': 'ROOT', 'protocol': 'rdp', 'attributes': {'guacd-encryption': None, 'failover-only': None, 'weight': None, 'max-connections': None, 'guacd-hostname': None, 'guacd-port': None, 'max-connections-per-user': None}, 'activeConnections': 0}
		"""
		url = self.urljoin(self.url,'api/session/data/{0}/connections/{1}'.format(self.dataSource, connectionIdentifier))
		r = requests.get(url,headers=self.headers,params={'token':self.token})
		return r.json()
	
	def connectionParameters(self,connectionIdentifier):
		"""get details about a particular connection
		connectionIdentifier is an integer, returned from listConnections.keys() or listConnections['id']['identifier']
		>>> r = requests.get('http://prod.guac.service.consul:8080/guacamole/api/session/data/postgresql/connections/44/parameters',headers=head,params={'token':token})
		>>> r.json()
		{'security': 'rdp', 'hostname': 'IPADDYHERE', 'password': 'PLAINTEXTPWDHERE', 'ignore-cert': 'true', 'port': '3389', 'username': 'testuser'}
		"""
		url = self.urljoin(self.url,'api/session/data/{0}/connections/{1}/parameters'.format(self.dataSource, connectionIdentifier))
		r = requests.get(url,headers=self.headers,params={'token':self.token})
		return r.json()
	def newConnection(self,data):
		""" data must be a dict like this:
		data = {'parentIdentifier': 'ROOT', 'name': 'test', 'protocol': 'rdp', 'parameters': {'port': '3389', 'ignore-cert': 'true', 'hostname': '10.99.8.22', 'password': 'LJelNHtEV', 'username': 'test_user', 'security': 'rdp'}, 'attributes': {'guacd-encryption': None, 'failover-only': None, 'weight': None, 'max-connections': None, 'guacd-hostname': None, 'guacd-port': None, 'max-connections-per-user': None}}
		>>> r = requests.post('/guacamole/api/session/data/postgresql/connections/',headers=head,params={'token':token},json=new)
		
		returns: 
		{'name': 'test', 'identifier': '61', 'parentIdentifier': 'ROOT', 'protocol': 'rdp', 'parameters': {'port': '3389', 'ignore-cert': 'true', 'hostname': '10.99.8.22', 'password': 'LJelNHtEV', 'username': 'test_user', 'security': 'rdp'}, 'attributes': {}, 'activeConnections': 0}
		"""
		url = self.urljoin(self.url,'api/session/data/{0}/connections'.format(self.dataSource))
		r = requests.post(url,headers=self.headers,params={'token':self.token},json=data)
		return r.json()
	
	def givePermissionToConnection(self,username,connectionID):
		""" give a user access to a connection.
		/api/session/data/postgresql/users/testuser/permissions?token=TOKENHERE'
		-X PATCH 
		[
			{
				"op":"add",
				"path":"/connectionPermissions/22",
				"value":"READ"
			}
		]

		returns:
			status 204, no data on success.
		"""
		url = self.urljoin(self.url,'api/session/data/{0}/users/{1}/permissions'.format(self.dataSource, username))
		data = [{
			"op":"add",
			"path":"/connectionPermissions/%s" % connectionID,
			"value":"READ"
			}
			]
		r = requests.patch(url,headers=self.headers,params={'token':self.token},json=data)
		if r.status_code == 204:
			return True
		return False

	def userDetails(self,username):
		"""return details of user, if exists, else None
		curl '/api/session/data/postgresql/users/amontejano%40yumaunion.org?token=TOKENHERE' -H 'Accept: application/json, text/plain, */*'
		"""
		url = self.urljoin(self.url,'api/session/data/{0}/users/{1}'.format(self.dataSource, self.urlescape(username)))
		log.debug("guac.userDetails:%s" % url)
		r = requests.get(url,headers=self.headers,params={'token':self.token},json={})
		if r.status_code == 404:
			return None
		return r.json()

	def auth(self,username, password):
		"""auth to Guacamole and return a token.
		username and password are both strings.
		"""
		form={'username': username, 'password': password}
		url = self.urljoin(self.url,'api/tokens')
		r = requests.post(url, data=form, headers=self.headers)
		# returns something like:
		# {'authToken': 'TOKENHERE', 'username': 'apiuser', 'dataSource': 'postgresql', 'availableDataSources': ['postgresql', 'postgresql-shared']}
		d = r.json()
		self.token = d['authToken']
		self.authuser = d['username']
		self.dataSource = d['dataSource']
		self.availableDataSources = d['availableDataSources']
		return self.token

def main(args):
	return 0
if __name__=='__main__':
	sys.exit(main(sys.argv))
