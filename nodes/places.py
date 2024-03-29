# ---------------started by pouria - date : 7/2/2022 ---------------#

from app.services.neo4j import driver

def Existance_Of_Place(place_name):
    with driver.session() as session:
        node = session.run("match (p:Place{Place_name:$place_name}) "
                           "where not exists (p.updated_at) and not exists(p.deleted_at) "
                           "return p",
                           place_name=place_name)
        if not node.data():
            return False
        return True


def Create_Places(Place_name, user_id):
    #print(Existance_Of_Place(Place_name))
    if not Existance_Of_Place(Place_name):
        with driver.session() as session:
            node = session.run(
                "match (u:User{id:$user_id})"
                " create (p:Place{Place_name:$Place_name,"
                " id: apoc.create.uuid(),"
                " created_at:datetime()}),"
                " (u) - [:Created_at{Created_at:datetime()}] -> (p)"
                " return p",
                Place_name=Place_name,
                user_id=user_id)
    else:
        return 'Error'


def Get_Places_by_USer_Id(user_id):
    with driver.session() as session:
        node = session.run("match (u:User{id:$user_id}) - [r] -> (p:Place) "
                           "where not exists (p.updated_at) and not exists(p.deleted_at) "
                           " return p",
                           user_id=user_id)
        result = []
        for each in node.data():
            result.append(each['p'])
        return result


def Show_Place_With_Id(place_id):
    with driver.session() as session:
        node = session.run("match (p:Place{id:$place_id}) "
                           "where not exists (p.updated_at) and not exists(p.deleted_at) "
                           "return p",
                           place_id=place_id)
        result = []
        for each in node.data():
            result.append(each['p'])
        return result


# def Delete_Place_With_Id(place_id):
#     with driver.session() as session:
#         session.run("match (p:Place{id:$place_id})"
#                     "detach delete p",
#                     place_id=place_id)

# ---------------ended by pouria - date : 7/2/2022 ---------------#

def find_places_by_device_id(devices_list_id):
    result = []
    with driver.session() as session:
        for device_id in devices_list_id:
            node = session.run("match (d:Device {id:$device_id}) <- [r] - (p:Place) "
                               "where not exists (p.updated_at) and not exists(p.deleted_at) "
                               "return p",
                               device_id=device_id)

            for each in node.data():
                result.append(each['p'])
        #print(result)
        return result