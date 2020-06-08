# Notes for DynamoDB data model

## Overview

We use a single table design to hold both layer and build items in one table. There is a single partition key(pk) and sort key(sk), shared between the two items. Hence, we use the generic names of pk and sk for both.

* Every layer entity has:
  * pk: lyr#\<rgn>.\<pckg>
  * sk: lyrVrsn#v\<version>
  * Additionally, every layer has a separate item for v0
    * pk: lyr#\<rgn>.\<pckg>
    * sk: lyrVrsn0#

* Every build entity has:
  * pk: bld#v\<version>
  * sk: pckg#\<package_name>
  * Additionally, every build has a separate item for v0
    * pk: bldVrsn0#
    * sk: pckg#\<package_name>

## Access Patterns

### Get Latest arn in region for package

* For every new layer insert, Update lyrVrsn0# to reflect
* Query rgnPckg and lyrVrsn0# to get latest version in region

### Get latest package for all regions

* Create a GSI with package and dplySts
* Query for GSI pckg and dplySts='latest'
* Note: dplySts exists only for active layers, hence this GSI is sparse

### Get all deployed layers in region

* Create GSI for rgn and dplySts
* Query for rgn only.
* We want both deprecated and latest
* Note: dplySts exists only for active layers, hence this GSI is sparse

### Get latest requirements.txt / requirementsHsh for package

* bld#v0
* package=package

### Get latest requirements.txt / requirementsHsh for all packages

* bld#v0, single query will return everything :)

### When deleting

* Remove dplySts field
* Add deleted_date field
* Re-insert into DB

### When inserting layer

* update lyrVrsn0#
* Insert row for currrent version
* Update previous layer dplySts='deprecated' & set TTL

### When inserting build

* update bldVrsn0#
* Insert item for currrent build

## DynamoDB Stream

We use a dynamoDB stream to delete the layer. This occurs when the item is deleted as a result of TTL expiration. The stream puts a message onto the eventrbridge.

From Eventbridge, we are only interested in the 'REMOVE' event for items with whose pk is prefixed with "lyr#". A lambda function takes the stream data and populates the record, pk prefix, and sk prefix onto the event bus.

From here, we use a single lambda, filtered on the following criteria to delete:

```yml
  events:
    - eventBridge:
        pattern:
          source:
            - ${self:custom.dbStreamLabel}
          detail-type:
            - REMOVE
          detail:
            pk_type:
              - "lyr"
```