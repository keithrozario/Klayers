# Get Latest arn in region for package
* Update #lyr.V0 for every new Insert as sk
* Query rgnPckg and #lyr.V0 to get latest version in region

## Sparse Index 1

### Get latest package for all regions
* Create a GSI with package and dplySts
* Query for GSI pckg and dplySts='latest'

## Sparse Index 2

### Get all deployed layers in region

* Create GSI for rgn and dplySts
* Query for rgn only.
* We want both deprecated and latest


When deleting:
+ Remove dplySts field
+ Add deleted_date field
+ Re-insert into DB

When inserting:
+ update #lyr.V0
+ Insert row for currrent version
* Update previous layer dplySts='deprecated' & set TTL

Get latest requirements.txt / requirementsHsh
* #bld.v0
* package=package
