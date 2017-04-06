Security Notes
==============

Overview
--------

Security in Orlo is on a "best-effort" basis. It has not been audited for security flaws, and its endpoints should 
be protected from hostile attackers.  The authentication/authorisation code has not been pentested, thus you 
should not rely on it to protect security-sensitive information.


Keep instances on private networks
----------------------------------

Orlo is intended to be run on a private, trusted network and should not be exposed publicly.


Keep instances isolated
-----------------------

Do not co-locate Orlo with sensitive information.


Cross-site scripting
--------------------

Orlo presently offers NO protection from cross-site scripting attacks. You should treat any data returned from Orlo as 
potentially hostile in any app that uses its output in a web browser


Third-party libraries
---------------------

Orlo uses third-party libraries for security-sensitive operations where possible.

