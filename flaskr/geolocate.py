from geopy.geocoders import Nominatim

import certifi, ssl, geopy.geocoders, geopy.distance

def get_loc():
    ctx = ssl.create_default_context(cafile=certifi.where())
    geopy.geocoders.options.default_ssl_context = ctx

    loc = Nominatim(user_agent='neighbor-chat')
    return loc

def locate(address):
    try:
        loc = get_loc()

        location = loc.geocode(address)
        
        if not location:
            raise TypeError
    except:
        print("Error: geocode failed on input %s" % (address))
        raise TypeError

    return location

def get_addr(address):
    return locate(address).address

def get_coord(address):
    return (locate(address).latitude, locate(address).longitude)

def find_coord(addr_street, addr_city, addr_state, addr_zip):
    addr = []
    addr.append(addr_street)
    addr.append(addr_city)
    addr.append(addr_state)
    addr.append(addr_zip)

    return get_coord(','.join(addr))

def get_distance(coord1, coord2):
    return geopy.distance.geodesic(coord1, coord2).miles

# Test command: python flaskr/geolocate.py
def main(address1, address2):
    print(address1)

    print(get_addr(address1))
    print(get_coord(address1))

    coord1 = get_coord(address1)
    coord2 = get_coord(address2)

    print(get_distance(coord1, coord2))

if __name__ == "__main__":
    main('Central Park South', '6 MetroTech')