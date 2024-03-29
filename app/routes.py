from app import app
from flask import render_template, request, make_response, redirect, send_file
from flask_wtf import FlaskForm
from wtforms import FileField
import json
import os
from datetime import date

from nodes import users as uFunc
from nodes import projects as pFunc
from nodes import experiments as exFunc
# from nodes import protocol as prFunc

from nodes import users as uFunc
from nodes import projects as pFunc
from nodes import standrad as sFunc
from nodes import places as placeFunc
from nodes import devices as deviceFunc
from nodes import protocol as protocolFunc
from nodes import BOMs as bomFunc
from nodes import tasks as taskFunc
from nodes import Results as resultFunc
from nodes import Folders_and_Files as folderFunc
from nodes import delete_nodes as delFunc
from nodes import update_nodes as updateFunc


@app.route('/', methods=['GET'])
def index():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    form = request.form.to_dict()
    userDict = uFunc.loginUser(userName=form['userName'], password=form['password'])
    resp = make_response(render_template('index.html'))
    resp.set_cookie("User_id", userDict['id'])
    return resp


@app.route('/index', methods=['GET'])
def show_dashboard():
    userId = request.cookies.get('User_id')
    if userId:
        resp = make_response(render_template('index.html'))
    else:
        resp = make_response(render_template('login.html'))
    return resp


@app.route('/projects', methods=['GET'])
def show_projects():
    userId = request.cookies.get('User_id')
    if not userId:
        resp = make_response(render_template('login.html'))
        return resp
    userProjects = pFunc.findUserProjects(userId)
    resp = make_response(render_template('projects.html', userProjects=userProjects))
    return resp


@app.route('/projects', methods=['post'])
def create_projects():
    userId = request.cookies.get('User_id')
    if not userId:
        resp = make_response(render_template('login.html'))
        return resp
    form = request.form.to_dict()
    pFunc.createProject(userId=userId, name=form['projectName'])
    userProjects = pFunc.findUserProjects(userId)
    resp = make_response(render_template('projects.html', userProjects=userProjects))
    return resp


@app.route("/projects/<id>", methods=['GET'])
def read_project(id):
    project = pFunc.getProjectById(id)
    experiments = pFunc.getProjectExperiments(id)
    users = uFunc.get_user()
    # print(users)
    resp = make_response(render_template('project.html', project=project, experiments=experiments, users=users, id=id))
    return resp


@app.route("/projectsdel/<id>", methods=['GET'])
def delete_project(id):
    delFunc.delete_node_by_id(id)
    userId = request.cookies.get('User_id')
    userProjects = pFunc.findUserProjects(userId)
    resp = make_response(render_template('projects.html', userProjects=userProjects))
    return resp


@app.route("/projects/<id>", methods=['POST'])
def update_project(id):
    userId = request.cookies.get('User_id')
    if not userId:
        resp = make_response(render_template('login.html'))
        return resp
    form = request.form.to_dict()
    dic = {}
    if form['projectName'] != '':
        dic['name'] = form['projectName']
    if dic != {}:
        node_id = updateFunc.copy_nodes(id)
        updateFunc.update_node(dic, node_id)
    else:
        node_id = id

    return redirect(f'/projects/{node_id}')

@app.route("/add_user_to_project/<id>", methods=['POST'])
def add_user_to_project(id):
    userId = request.cookies.get('User_id')
    if not userId:
        resp = make_response(render_template('login.html'))
        return resp
    form = request.form.to_dict(flat=False)
    if form['user_list'] != [] and form['permission'] != []:
        for u in form['user_list']:
            for p in form['permission']:
                pFunc.connect_user_to_project(id, u, p)
    return redirect(f'/projects/{id}')



@app.route("/delete_experiment/<id>", methods=['GET'])
def delete_experiment(id):
    userId = request.cookies.get('User_id')
    if not userId:
        resp = make_response(render_template('login.html'))
        return resp
    project_id = exFunc.find_project_by_experiment_id(id)[0]
    delFunc.delete_node_by_id(id)
    return redirect(f'/projects/{project_id}')


@app.route("/experiment/<id>", methods=['POST'])
def update_experiment(id):
    userId = request.cookies.get('User_id')
    if not userId:
        resp = make_response(render_template('login.html'))
        return resp
    form = request.form.to_dict()
    dic = {}
    print(form)
    if form['name'] != '':
        dic['name'] = form['name']
    if dic != {}:
        node_id = updateFunc.copy_nodes(id)
        updateFunc.update_node(dic, node_id)
    else:
        node_id = id
    return redirect(f'/experiment/{node_id}')


@app.route("/experiment", methods=['POST'])
def makeExperiment():
    userId = request.cookies.get('User_id')
    form = request.form.to_dict()
    exFunc.createExperiment(form['projectId'], form['experimentName'])
    project = pFunc.getProjectById(form['projectId'])
    experiments = pFunc.getProjectExperiments(form['projectId'])
    resp = make_response(render_template('project.html', project=project, experiments=experiments))
    return resp


@app.route('/experiment/<id>', methods=['GET'])
def read_experiment(id):
    experiment = exFunc.getExperimentById(id)

    # my_tree = exFunc.getTree(id)
    my_tree = exFunc.getTree_Pouria(id, 'Protocol')

    if len(my_tree[0]) == 0:
        tree_levels = [0]
    else:
        tree_levels = list(my_tree[0].keys())
    tree_dict = my_tree[0]
    tree_graph = my_tree[1]
    protocols = {}
    for each in tree_dict:
        protocols[each] = []
        for every in tree_dict[each]:
            # print(tree_graph.nodes[every])
            protocols[each].append(tree_graph.nodes[every])
    # del(protocols[0])
    if 0 in protocols:
        del (protocols[0])
    experiment_id = id
    results = resultFunc.find_result_by_experiment_id(id)

    res = make_response(
        render_template('experiment.html',
                        experiment=experiment,
                        tree_levels=tree_levels,
                        protocols=protocols,
                        experiment_id=experiment_id,
                        results=results))

    return res


@app.route('/add_results', methods=['POST'])
def add_results():
    userId = request.cookies.get('User_id')
    if not userId:
        resp = make_response(render_template('login.html'))
        return resp
    form = request.form.to_dict()
    # **************
    if form['result_name'] != '' and form['content'] != '':
        if not resultFunc.existance_of_result_name(form['result_name']):
            result_id = resultFunc.create_result(form["experiment_id"], form['result_name'], form['content'])
            if not request.files['file'].filename == '':
                today = str(date.today()).split('-')
                day = today[-1]
                month = today[1]
                year = today[0]
                path = os.getcwd()+f"\\app\\templates\\vendors\\files\\{year}\\{month}\\{day}\\{form['result_name']}"
                if not os.path.isdir(path):
                    os.makedirs(path)
                file = request.files.getlist('file')
                for file in file:
                    app.config['UPLOAD_FOLDER'] = path
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
                    final_path = path + '\\' + file.filename
                    folderFunc.add_file_to_result(final_path, file.filename, result_id)



        # print(result_id)

        # **************

    return redirect(f'/experiment/{form["experiment_id"]}')


@app.route('/Results/<id>', methods=['GET'])
def show_results(id):
    userId = request.cookies.get('User_id')
    if not userId:
        resp = make_response(render_template('login.html'))
        return resp

    all_paths, videos, images, audios = resultFunc.format_seperator(id)
    # print('audios = ', audios)
    # print('images = ', images)
    # print('videos = ', videos)
    # print('all_paths = ', all_paths)
    files_info = resultFunc.get_files_by_result_id(id)
    result = resultFunc.get_result_by_id(id)
    # print(files_info)
    # print('*********************\n\n\n', result)
    res = make_response(render_template('/Results.html',
                                        videos=videos,
                                        images=images,
                                        audios=audios,
                                        files_info=files_info,
                                        result=result,
                                        result_id=id))
    return res


@app.route('/download_file/<id>/<result_id>', methods=['GET'])
def download(id, result_id):
    userId = request.cookies.get('User_id')
    if not userId:
        resp = make_response(render_template('login.html'))
        return resp
    file_info = resultFunc.give_path_by_file_id(id)
    path = file_info[0]['path'].replace('\\', '/')
    return send_file(path, as_attachment=True)

@app.route('/delete_result/<id>')
def delete_result(id):
    userId = request.cookies.get('User_id')
    if not userId:
        resp = make_response(render_template('login.html'))
        return resp
    experiment_id = resultFunc.get_experiment_by_result_id(id)
    delFunc.delete_node_by_id(id)
    return redirect(f'/experiment/{experiment_id[0]}')


@app.route('/update_result/<id>', methods=['POST'])
def update_result(id):
    userId = request.cookies.get('User_id')
    if not userId:
        resp = make_response(render_template('login.html'))
        return resp
    form = request.form.to_dict()
    dic = {}
    #print(form, '***********\n\n\n\n\n\n')
    if form['name'] != '':
        dic['result_name'] = form['name']
    if dic != {}:
        node_id = updateFunc.copy_nodes(id)
        updateFunc.update_node(dic, node_id)
    else:
        node_id = id
    return redirect(f'/Results/{node_id}')

@app.route('/protocols', methods=['POST'])
def create_protocol():
    data = request.form.to_dict()
    experiment = exFunc.getExperimentById(data["experiment_id"])
    protocol_id = protocolFunc.make_protocol(data['name'])

    # my_tree = exFunc.getTree(data["experiment_id"])
    my_tree = exFunc.getTree_Pouria(data["experiment_id"], 'Protocol')

    tree_level = data['tree_level']
    tree_level = int(tree_level)
    if len(my_tree[0]) == 0:
        tree_levels = [0]
        protocolFunc.connect_to_idies(protocol_id, [experiment['id']])
    else:
        parent_list = my_tree[0][tree_level]
        parent_idies = []
        for each in parent_list:
            parent_idies.append(my_tree[1].nodes[each]['properties']['id'])
        protocolFunc.connect_to_idies(protocol_id, parent_idies)
        # tree_levels = list(my_tree[0].keys())
    # tree_dict = my_tree[0]
    # tree_graph = my_tree[1]
    # protocols = {}
    # for each in tree_dict:
    #     protocols[each] = []
    #     for every in tree_dict[each]:
    #         protocols[each].append(tree_graph.nodes[every])
    # # del(protocols[0])
    #
    # if 0 in protocols:
    #     del (protocols[0])

    # res = make_response(
    # render_template('experiment.html', experiment=experiment, tree_levels=tree_levels, protocols=protocols))

    return redirect(f'/experiment/{data["experiment_id"]}')

    # return res


@app.route('/create_account', methods=['POST'])
def make_account():
    data = request.form.to_dict()
    uFunc.create_user(data)
    return {"response": "user created"}


# ---------------started by pouria - date : 6/2/2022 ---------------# #
@app.route("/projects_standard", methods=['GET'])
def show_standards():
    userId = request.cookies.get('User_id')
    if not userId:
        resp = make_response(render_template('login.html'))
        return resp
    userProjects = pFunc.findUserProjects(userId)
    standard = sFunc.Get_Standard_by_USer_Id(userId)
    resp = make_response(render_template('standard_form.html',
                                         userProjects=userProjects,
                                         standard=standard))
    return resp


@app.route('/projects_standard', methods=['post'])
def add_standards():
    userId = request.cookies.get('User_id')
    if not userId:
        resp = make_response(render_template('login.html'))
        return resp
    form = request.form.to_dict()
    sFunc.Create_Standards(form['standard_content'], form['project_id'], form["standard_name"])
    userProjects = pFunc.findUserProjects(userId)
    # resp = make_response(render_template('standard_form.html', userProjects=userProjects))
    # return resp
    return redirect('/projects_standard')


@app.route('/delete_standards/<id>')
def delete_standards(id):
    userId = request.cookies.get('User_id')
    if not userId:
        resp = make_response(render_template('login.html'))
        return resp
    delFunc.delete_node_by_id(id)
    return redirect('/projects_standard')


@app.route('/update_standard/<standard_id>', methods=['GET'])
def update_form_standard(standard_id):
    userId = request.cookies.get('User_id')
    if not userId:
        resp = make_response(render_template('login.html'))
        return resp
    resp = make_response(render_template('update_standard.html',
                                         standard_id=standard_id))
    return resp

@app.route('/update_standard/<standard_id>', methods=['post'])
def update_standard(standard_id):
    userId = request.cookies.get('User_id')
    if not userId:
        resp = make_response(render_template('login.html'))
        return resp
    form = request.form.to_dict()
    dic = {}
    print(form,'***********\n\n\n\n')
    if form['standard_name'] != '':
        dic['Standard_name'] = form['standard_name']

    if form['standard_content'] != '':
        dic['Content'] = form['standard_content']

    print(dic)

    if dic != {}:
        node_id = updateFunc.copy_nodes(standard_id)
        updateFunc.update_node(dic, node_id)

    return redirect(f'/projects_standard')

# @app.route()
# def update_standards(id):

# ---------------started by pouria - date : 6/2/2022 ---------------#

# ---------------started by pouria - date : 7/2/2022 ---------------#

@app.route("/Places", methods=['GET'])
def show_Places():
    userId = request.cookies.get('User_id')
    if not userId:
        resp = make_response(render_template('login.html'))
        return resp
    places = placeFunc.Get_Places_by_USer_Id(userId)
    resp = make_response(render_template('Places.html', places=places))
    return resp


@app.route('/Places', methods=['post'])
def add_places():
    userId = request.cookies.get('User_id')
    if not userId:
        resp = make_response(render_template('login.html'))
        return resp
    form = request.form.to_dict()
    placeFunc.Create_Places(form['Place_Name'], userId)
    places = placeFunc.Get_Places_by_USer_Id(userId)
    resp = make_response(render_template('Places.html', places=places))
    return resp


@app.route("/Places/<id>", methods=['GET'])
def read_place(id):
    place = placeFunc.Show_Place_With_Id(id)[0]
    device = deviceFunc.Get_Devices_By_Place_Id(id)
    resp = make_response(render_template('Place.html', place=place, device=device))
    return resp


@app.route('/delete_place/<id>')
def delete_place(id):
    userId = request.cookies.get('User_id')
    if not userId:
        resp = make_response(render_template('login.html'))
        return resp
    #placeFunc.Delete_Place_With_Id(id)
    delFunc.delete_node_by_id(id)
    places = placeFunc.Get_Places_by_USer_Id(userId)
    resp = make_response(render_template('Places.html', places=places))
    return resp

@app.route("/update_place/<id>", methods=['POST'])
def update_place(id):
    userId = request.cookies.get('User_id')
    if not userId:
        resp = make_response(render_template('login.html'))
        return resp
    form = request.form.to_dict()
    dic = {}
    if form['Place_Name'] != '':
        dic['Place_name'] = form['Place_Name']
    if dic != {}:
        node_id = updateFunc.copy_nodes(id)
        updateFunc.update_node(dic, node_id)
    return redirect(f'/Places')


@app.route('/Devices', methods=['GET'])
def show_devices():
    userId = request.cookies.get('User_id')
    if not userId:
        resp = make_response(render_template('login.html'))
        return resp
    Lab = placeFunc.Get_Places_by_USer_Id(userId)
    devices = deviceFunc.Get_Device_by_USer_Id(userId)
    resp = make_response(render_template('Devices.html',
                                         Lab=Lab,
                                         devices=devices))
    return resp


@app.route('/Devices', methods=['post'])
def add_devices():
    userId = request.cookies.get('User_id')
    if not userId:
        resp = make_response(render_template('login.html'))
        return resp
    form = request.form.to_dict()
    deviceFunc.Create_Devices(form['device_name'], form['device_description'], form['device_id'], form['place_id'])
    Lab = placeFunc.Get_Places_by_USer_Id(userId)
    resp = make_response(render_template('Devices.html', Lab=Lab))
    return resp


@app.route('/delete_device/<id>')
def delete_device(id):
    userId = request.cookies.get('User_id')
    if not userId:
        resp = make_response(render_template('login.html'))
        return resp
    #deviceFunc.Delete_Device_By_Id(id)
    delFunc.delete_node_by_id(id)
    places = placeFunc.Get_Places_by_USer_Id(userId)
    resp = make_response(render_template('Places.html', places=places))
    return resp



@app.route('/update_device/<device_id>/<place_id>', methods=['GET'])
def update_form_devices(device_id, place_id):
    userId = request.cookies.get('User_id')
    if not userId:
        resp = make_response(render_template('login.html'))
        return resp
    resp = make_response(render_template('update_device.html',
                                         device_id=device_id,
                                         place_id=place_id))
    return resp


@app.route('/update_device/<device_id>/<place_id>', methods=['post'])
def update_device(device_id, place_id):
    userId = request.cookies.get('User_id')
    if not userId:
        resp = make_response(render_template('login.html'))
        return resp
    form = request.form.to_dict()
    dic = {}
    #print(form,'***********\n\n\n\n')
    if form['device_name'] != '':
        dic['device_name'] = form['device_name']

    if form['device_id'] != '' and not deviceFunc.Existance_of_Device_Id(form['device_id']):
        dic['device_id'] = form['device_id']

    if form['device_description'] != '':
        dic['device_description'] = form['device_description']

    if dic != {}:
        node_id = updateFunc.copy_nodes(device_id)
        updateFunc.update_node(dic, node_id)
    #print(dic)
    return redirect(f'/Places/{place_id}')


# ---------------ended by pouria - date : 7/2/2022 ---------------#

# ---------------started by pouria - date : 7/2/2022 ---------------#
# @app.route("/Protocols", methods=['GET'])
# def show_Porotocols():
#     userId = request.cookies.get('User_id')
#     if not userId:
#         resp = make_response(render_template('login.html'))
#         return resp
#
#     protocols = protocolFunc.Get_Protocols_by_USer_Id(userId)
#     devices = deviceFunc.Get_Device_by_USer_Id(userId)
#     standard = sFunc.Get_Standard_by_USer_Id(userId)
#     BOM = bomFunc.Get_BOMs_by_USer_Id(userId)
#
#     resp = make_response(render_template('Protocols.html',
#                                          protocols=protocols,
#                                          devices=devices,
#                                          standard=standard,
#                                          BOM=BOM))
#     return resp
#
#
# @app.route('/Protocols', methods=['post'])
# def add_protocols():
#     userId = request.cookies.get('User_id')
#     if not userId:
#         resp = make_response(render_template('login.html'))
#         return resp
#     form = request.form.to_dict()
#     protocolFunc.create_Protocol(form['Protocol_Name'], form['id'], userId)
#
#     protocols = protocolFunc.Get_Protocols_by_USer_Id(userId)
#     devices = deviceFunc.Get_Device_by_USer_Id(userId)
#     standard = sFunc.Get_Standard_by_USer_Id(userId)
#     BOM = bomFunc.Get_BOMs_by_USer_Id(userId)
#
#     resp = make_response(render_template('Protocols.html',
#                                          protocols=protocols,
#                                          devices=devices,
#                                          standard=standard,
#                                          BOM=BOM))
#     return resp


# ---------------ended by pouria - date : 7/2/2022 ---------------#
# ---------------started by pouria - date : 7/2/2022 ---------------#

@app.route("/Protocols/<id>", methods=['GET'])
def read_protocol(id):
    userId = request.cookies.get('User_id')
    if not userId:
        resp = make_response(render_template('login.html'))
        return resp
    standards_list = protocolFunc.get_standards_by_protocol_id(id)
    device_list = protocolFunc.get_device_by_protocol_id(id)
    BOM_list = protocolFunc.get_BOM_by_protocol_id(id)
    standards = sFunc.Get_Standard_by_USer_Id(userId)
    user_boms = bomFunc.Get_BOMs_by_USer_Id(userId)
    devices = deviceFunc.Get_Device_by_USer_Id(userId)
    tasks = taskFunc.get_tasks_by_protocol_id(id)
    place_names = placeFunc.find_places_by_device_id(protocolFunc.get_id_device_by_protocol_id(id))
    resp = make_response(render_template('Protocol.html',
                                         standards_list=standards_list,
                                         device_list=device_list,
                                         BOM_list=BOM_list,
                                         standards=standards,
                                         protocol_id=id,
                                         user_boms=user_boms,
                                         devices=devices,
                                         tasks=tasks,
                                         place_names=place_names))
    return resp


@app.route("/delete_protocol/<id>", methods=['GET'])
def delete_protocol(id):
    userId = request.cookies.get('User_id')
    if not userId:
        resp = make_response(render_template('login.html'))
        return resp
    experiment_id = protocolFunc.get_protocol_by_result_id(id)
    delFunc.delete_node_by_id(id)
    return redirect(f'/experiment/{experiment_id}')

# ---------------ended by pouria - date : 7/2/2022 ---------------#

# ---------------started by pouria - date : 7/2/2022 ---------------#

@app.route("/BOMs", methods=['GET'])
def show_BOMs():
    userId = request.cookies.get('User_id')
    if not userId:
        resp = make_response(render_template('login.html'))
        return resp
    bom_names = bomFunc.Get_BOMs_by_USer_Id(userId)
    resp = make_response(render_template('BOMs.html',
                                         bom_names=bom_names))
    return resp


@app.route('/BOMs', methods=['post'])
def add_BOMs():
    userId = request.cookies.get('User_id')
    if not userId:
        resp = make_response(render_template('login.html'))
        return resp
    form = request.form.to_dict(flat=False)
    if 'BOM_id_List' not in form:
        form['BOM_id_List'] = []
    BOM_value = form['BOM_Values'][0].split('-')
    if form['BOM_Values'] == ['']:
        BOM_value = form['BOM_Values'] = []
    if len(form['BOM_id_List']) == len(BOM_value):
        bomFunc.Create_BOM(userId,
                           form['BOM_id_List'],
                           form['BOM_Name'][0],
                           form['BOM_Description'][0],
                           BOM_value,
                           form['ph'][0],
                           form['volume'][0],
                           form['Type_of_material'][0])
    bom_names = bomFunc.Get_BOMs_by_USer_Id(userId)
    return redirect('/BOMs')


@app.route('/delete_boms/<id>')
def delete_boms(id):
    userId = request.cookies.get('User_id')
    if not userId:
        resp = make_response(render_template('login.html'))
        return resp
    delFunc.delete_node_by_id(id)
    return redirect('/BOMs')


@app.route('/update_bom/<bom_id>', methods=['GET'])
def update_form_BOM(bom_id):
    userId = request.cookies.get('User_id')
    if not userId:
        resp = make_response(render_template('login.html'))
        return resp
    resp = make_response(render_template('update_BOM.html',
                                         bom_id=bom_id))
    return resp


@app.route('/update_bom/<bom_id>', methods=['post'])
def update_BOM(bom_id):
    userId = request.cookies.get('User_id')
    if not userId:
        resp = make_response(render_template('login.html'))
        return resp
    form = request.form.to_dict()
    dic = {}
    #print(form,'***********\n\n\n\n')
    if form['BOM_Description'] != '':
        dic['description'] = form['BOM_Description']

    if form['BOM_Name'] != '' and not bomFunc.Existance_of_BOM(form['BOM_Name']):
        dic['BOM_name'] = form['BOM_Name']

    if form['ph'] != '':
        dic['ph'] = form['ph']

    if form['volume'] != '':
        dic['volume'] = form['volume']

    if form['Type_of_material'] != '':
        dic['Type_of_material'] = form['Type_of_material']

    if dic != {}:
        node_id = updateFunc.copy_nodes(bom_id)
        updateFunc.update_node(dic, node_id)
    #print(dic)
    return redirect(f'/BOMs')


# -----------------added by hossein 2/23/2022--------------
@app.route('/add_standard_to_protocol', methods=['post'])
def add_standard_to_protocol():
    userId = request.cookies.get('User_id')
    if not userId:
        resp = make_response(render_template('login.html'))
        return resp
    form = request.form.to_dict(flat=False)
    id = form['protocol_id'][0]
    protocolFunc.connect_to_idies(id, form['standard_list'])

    return redirect(f'/Protocols/{id}')
    # standards_list = protocolFunc.get_standards_by_protocol_id(id)
    # device_list = protocolFunc.get_device_by_protocol_id(id)
    # BOM_list = protocolFunc.get_BOM_by_protocol_id(id)
    # standards = sFunc.Get_Standard_by_USer_Id(userId)
    # user_boms = bomFunc.Get_BOMs_by_USer_Id(userId)
    # devices = deviceFunc.Get_Device_by_USer_Id(userId)
    # tasks = taskFunc.get_tasks_by_protocol_id(id)
    # place_names = placeFunc.find_places_by_device_id(protocolFunc.get_id_device_by_protocol_id(id))
    # resp = make_response(render_template('Protocol.html',
    #                                      standards_list=standards_list,
    #                                      device_list=device_list,
    #                                      BOM_list=BOM_list,
    #                                      standards=standards,
    #                                      protocol_id=id,
    #                                      user_boms=user_boms,
    #                                      devices=devices,
    #                                      tasks=tasks,
    #                                      place_names=place_names))
    #
    # return resp


@app.route('/add_bom_to_protocol', methods=['post'])
def add_bom_to_protocol():
    userId = request.cookies.get('User_id')
    if not userId:
        resp = make_response(render_template('login.html'))
        return resp
    form = request.form.to_dict(flat=False)
    id = form['protocol_id'][0]
    protocolFunc.connect_to_idies(id, form['bom_list'])
    return redirect(f'/Protocols/{id}')
    # standards_list = protocolFunc.get_standards_by_protocol_id(id)
    # device_list = protocolFunc.get_device_by_protocol_id(id)
    # BOM_list = protocolFunc.get_BOM_by_protocol_id(id)
    # standards = sFunc.Get_Standard_by_USer_Id(userId)
    # tasks = taskFunc.get_tasks_by_protocol_id(id)
    # user_boms = bomFunc.Get_BOMs_by_USer_Id(userId)
    # devices = deviceFunc.Get_Device_by_USer_Id(userId)
    # place_names = placeFunc.find_places_by_device_id(protocolFunc.get_id_device_by_protocol_id(id))
    #
    # resp = make_response(render_template('Protocol.html',
    #                                      standards_list=standards_list,
    #                                      device_list=device_list,
    #                                      BOM_list=BOM_list,
    #                                      standards=standards,
    #                                      protocol_id=id,
    #                                      user_boms=user_boms,
    #                                      devices=devices,
    #                                      tasks=tasks,
    #                                      place_names=place_names))
    #
    # return resp


@app.route('/add_device_to_protocol', methods=['post'])
def add_device_to_protocol():
    userId = request.cookies.get('User_id')
    if not userId:
        resp = make_response(render_template('login.html'))
        return resp

    form = request.form.to_dict(flat=False)
    protocolFunc.connect_to_idies(form['protocol_id'][0], form['devices_id_List'])
    protocol_id = form['protocol_id'][0]
    return redirect(f'/Protocols/{protocol_id}')
    # place_names = placeFunc.find_places_by_device_id(protocolFunc.get_id_device_by_protocol_id(protocol_id))
    # standards_list = protocolFunc.get_standards_by_protocol_id(protocol_id)
    # device_list = protocolFunc.get_device_by_protocol_id(protocol_id)
    # BOM_list = protocolFunc.get_BOM_by_protocol_id(protocol_id)
    # devices = deviceFunc.Get_Device_by_USer_Id(userId)
    # standards = sFunc.Get_Standard_by_USer_Id(userId)
    # tasks = taskFunc.get_tasks_by_protocol_id(protocol_id)
    # user_boms = bomFunc.Get_BOMs_by_USer_Id(userId)
    # resp = make_response(render_template('Protocol.html',
    #                                      standards_list=standards_list,
    #                                      device_list=device_list,
    #                                      BOM_list=BOM_list,
    #                                      devices=devices,
    #                                      standards=standards,
    #                                      protocol_id=protocol_id,
    #                                      user_boms=user_boms,
    #                                      tasks=tasks,
    #                                      place_names=place_names))
    # return resp


@app.route('/add_task_to_protocol', methods=['post'])
def add_task_to_protocol():
    userId = request.cookies.get('User_id')
    if not userId:
        resp = make_response(render_template('login.html'))
        return resp
    form = request.form.to_dict()
    id = form['protocol_id']
    taskFunc.create_tasks(form['task'].split('\r\n'), id)
    return redirect(f'/Protocols/{id}')
    # tasks = taskFunc.get_tasks_by_protocol_id(id)
    # place_names = placeFunc.find_places_by_device_id(protocolFunc.get_id_device_by_protocol_id(id))
    # standards_list = protocolFunc.get_standards_by_protocol_id(id)
    # device_list = protocolFunc.get_device_by_protocol_id(id)
    # BOM_list = protocolFunc.get_BOM_by_protocol_id(id)
    # standards = sFunc.Get_Standard_by_USer_Id(userId)
    # user_boms = bomFunc.Get_BOMs_by_USer_Id(userId)
    # devices = deviceFunc.Get_Device_by_USer_Id(userId)
    # resp = make_response(render_template('Protocol.html',
    #                                      standards_list=standards_list,
    #                                      device_list=device_list,
    #                                      BOM_list=BOM_list,
    #                                      standards=standards,
    #                                      protocol_id=id,
    #                                      user_boms=user_boms,
    #                                      devices=devices,
    #                                      tasks=tasks,
    #                                      place_names=place_names))
    #
    # return resp


@app.route("/Folders", methods=['GET'])
def show_Folders():
    userId = request.cookies.get('User_id')
    if not userId:
        resp = make_response(render_template('login.html'))
        return resp
    folder_names = folderFunc.get_folder_name()
    resp = make_response(render_template('Folders.html',
                                         folder_names=folder_names))
    return resp


@app.route("/Folders", methods=['POST'])
def add_Folders():
    userId = request.cookies.get('User_id')
    if not userId:
        resp = make_response(render_template('login.html'))
        return resp

    form = request.form.to_dict()
    #print(form)
    if 'Top_Folder' not in form:
        form['Top_Folder'] = '[]'

    if form['file_or_folder'] == 'Folder':

        if form['Top_Folder'] == '[]':
            folderFunc.Create_Folder(form['Folder_or_File_name'], [], userId)
        else:
            folderFunc.Create_Folder(form['Folder_or_File_name'], form['Top_Folder'], userId)
    # else:
    #
    #     today = str(date.today()).split('-')
    #     day = today[-1]
    #     month = today[1]
    #     year = today[0]
    #     path = os.getcwd()+f"\\app\\templates\\vendors\\folders\\{year}\\{month}\\{day}"
    #     if not os.path.isdir(path):
    #         os.makedirs(path)
    #     file = request.files['file']
    #     if file:
    #         file_format = str(file.filename).split('.')[-1]
    #         app.config['UPLOAD_FOLDER'] = path
    #         file.save(os.path.join(app.config['UPLOAD_FOLDER'], form['Folder_or_File_name'] + '.' + file_format))
    #         final_path = path + '\\' + form['Folder_or_File_name'] + '.' + file_format
    elif not request.files['file'].filename == '':
        today = str(date.today()).split('-')
        day = today[-1]
        month = today[1]
        year = today[0]
        path = os.getcwd() + f"\\app\\templates\\vendors\\folders\\{year}\\{month}\\{day}\\{form['Folder_or_File_name']}"
        if not os.path.isdir(path):
            os.makedirs(path)
        file = request.files.getlist('file')
        for file in file:
            app.config['UPLOAD_FOLDER'] = path
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
            final_path = path + '\\' + file.filename
            folderFunc.Create_File(file.filename, final_path, form['Top_Folder'], userId)
    return redirect(f'/Folders')

    #         folderFunc.Create_File(form['Folder_or_File_name'], final_path, form['Top_Folder'], userId)
    # return redirect(f'/Folders')


@app.route("/Folder/<id>", methods=['GET'])
def what_inside_folders(id):
    userId = request.cookies.get('User_id')
    if not userId:
        resp = make_response(render_template('login.html'))
        return resp
    a = folderFunc.show_what_inside_folder(id)
    #print(a)
    folder_names = folderFunc.get_folder_name()
    resp = make_response(render_template('Folders.html',
                                         folder_names=folder_names))
    return resp
