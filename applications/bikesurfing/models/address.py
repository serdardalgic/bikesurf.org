# coding: utf8


db.define_table(
    'address',
    
    Field('street', 'string'),
    Field('city' 'string'),
    Field('postalcode' 'string'),
    Field('country' 'string'),
    
    Field('created_on','datetime',default=request.now,
          label=T('Created On'),writable=False,readable=False),
    Field('modified_on','datetime',default=request.now,
          label=T('Modified On'),writable=False,readable=False,
          update=request.now),
    
    format = 'Street: %(street)s; City: %(city)s; Postalcode: %(postalcode)s; Country: %(country)s',
    singular = 'Address',
    plural = 'Addresses',
)

# TODO bike location, organisation locations
