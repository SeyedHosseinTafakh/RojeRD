from app.services.neo4j import driver


def create_result(experiment_id, result_name, text):

    with driver.session() as session:
        node = session.run("match (e:Experiment {id:$experiment_id}) "
                           "create (r:Result {experiment_name:e.name, "
                           "result_name:$result_name, "
                           "id: apoc.create.uuid(), "
                           "created_at:datetime() ,"
                           "content:$text}) "
                           "create (e) - [:Created_at{Created_at:datetime()}] -> (r)",
                           experiment_id=experiment_id,
                           text=text,
                           result_name=result_name)

def find_result_by_experiment_id(experiment_id):

    with driver.session() as session:
        node = session.run("match (e:Experiment {id:$experiment_id}) - [rel] -> (r:Result)"
                           " return r",
                           experiment_id=experiment_id)
        result = []
        for each in node.data():
            result.append(each['r'])
        return result