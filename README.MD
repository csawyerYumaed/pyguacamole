# Apache Guacamole API code for python.

This code is terrible, but it works with Guacamole 1.3.0.

This is not a "python project" structured repo, it's just the guacamole file I created to get the job done, that sits within our local private repo that handles this stuff.

audit's have not been done, this is not for "production" at this point.

to use this code, just copy the guacamole.py file into your project, and then start a Guac() object, and call guac.Function() with information.

This requires the requests library(https://docs.python-requests.org/en/master/) and python3 (tested against Python 3.6.9).

The user permissions required:
```
Administer system:
Create new users:
Create new user groups:
Create new connections:
Create new connection groups:
```

examples:

```python
from guacamole import Guac
import pprint

guac = Guac()
#authenticate to Guacamole and get a token.
guac.auth('apiuser','apipassword')

# setup user information.
user = 'tootie'
user_password = 'SUPERSECRETPASSWORDHERE'
first_name = 'Tootie'
last_name = 'Jones'
user_id = '1234'

guac_user = guac.userDetails(user)
if not guac_user:
      # Guac user does not exist, add it
			connectionData = {
				'parentIdentifier': 'ROOT',
				'name': user,
				'protocol': 'rdp',
				'parameters': {
					'port': '3389',
					'ignore-cert': 'true',
					'hostname': '127.0.0.1',
					'password': user_password,
					'username': user,
					'security': 'rdp'
					},
				'attributes': {
					'guacd-encryption': None,
					'failover-only': None,
					'weight': None,
					'max-connections': None,
					'guacd-hostname': None, 
					'guacd-port': None, 
					'max-connections-per-user': None
					}
					}
			# add connection first.
			connectionData = guac.newConnection(connectionData)
      pprint.pprint(connectionData)
			#get connection ID so we can give permissions to connection after we create user.
			connectionID = connectionData['identifier']
			userData = {
						"username":user,
						"password":user_password,
						"attributes":{
							"disabled":"",
							"expired":"",
							"access-window-start":"",
							"access-window-end":"",
							"valid-from":"",
							"valid-until":"",
							"timezone":None,
							"guac-full-name":"%s %s" % (first_name, last_name),
							"guac-email-address":user_email,
							"guac-organizational-role":user_id
							}
				}

			pprint.pprint(userData))
			userData = guac.addUser(userData)
			print("giving %s permission to %s" % (user,connectionID))
			assert guac.givePermissionToConnection(user,connectionID)
```