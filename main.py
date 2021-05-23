import http.client
import json
import math
import time
from random import random
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from flask import Flask, redirect,url_for, render_template, request, jsonify
import queue
import threading
from concurrent.futures import ThreadPoolExecutor
import ast
import boto3




app = Flask(__name__)
cred = credentials.Certificate("myCredentials.json")
firebase_admin.initialize_app(cred)

db = firestore.client() # function setting up the database

queue = queue.Queue() # queue is synchronized, so caters for multiple threads
# count = 1000
# important = []
max_tries = 2
results=[]



@app.route("/reset")
def reset():
    results = []
    jsonify({'data':results})



# function for truncting the pi values
def truncate(f, digits):

    return ("{:.30f}".format(f))[:-30+digits]


@app.route("/<srvce>/<R>",methods = ["POST","GET"])
def getRDQS(srvce,R):
    print("servce and r: ",srvce,R)
    total_attempts = 5 # maximum number of times the system will resend the request
    if request.method == "POST":
        S = int(request.form["number_of_shots"])
        Q = int(request.form["reporting_rate"])
        D = int(request.form["matching_digits"])

        return redirect(url_for("results",service=srvce,R=R,D=D,Q=Q,S=S))

    else:
        return render_template("getRDQS.html")



@app.route("/",methods = ["POST","GET"])
def index(): # function for defining the post and get method
    if request.method == "POST":
        selected_service = request.form["radiobutton"]
        resources = request.form["resources"]
        print("Selected: ",selected_service)


        return redirect(url_for("getRDQS",srvce=selected_service,R=resources))

    else:
        return render_template("index.html")


@app.route("/<service>/<R>/<D>/<Q>/<S>",methods = ["POST","GET"])
def results(service,R,D,Q,S):# this session is defining the results
    eR = math.ceil(int(S)/int(R))
    incircle=0
    shot = 0
    pi_estimate = 0
    pi_estimations = []
    incircle_shot=[]
    elapsed_time = []
    global results
    max_tries = 3
    results = []
    pi_values=[]

    if service == "lambda":# this function is calling for the lambda

        while max_tries > 0:
            with ThreadPoolExecutor() as executor:
            # results exectute
                runs=[value for value in range(int(R))]


            for i in runs:

                try:

                    host = "dfx13yvwol.execute-api.us-east-1.amazonaws.com"
                    c = http.client.HTTPSConnection(host)
                    data = {
                        'pid': i,
                            "D":D,
                            "Q":Q,
                            "S":eR
                        }
                    # start = time.time()
                    c.request("POST", "/default/my_incircle_and_shot_values", json.dumps(data))
                    response = c.getresponse()


                    data = json.loads(response.read().decode('utf-8') )

                    if "errorMessage" in data:
                        print("Error from AWS")
                    else:
                        results.append(data)




                except IOError:
                    print( 'Failed to open ', host ) # Is the Lambda address correct?
                    print(data+" from "+str(i)) # May expose threads as completing in a different order
                    return "page "+str(i)


            for i in results:

                elapsed_time.append(ast.literal_eval(i['elapsed_time']))

                for j in ast.literal_eval(i['values']):
                    incircle = j[0] + incircle
                    shot = j[1] + shot
                    pie = (j[0]/j[1]) * 4
                    pi_estimations.append(pie)
                    incircle_shot.append([i["thread_id"],j[0],j[1]])


            pi_estimate = (incircle/shot)*4
            truncated_pi_estimate = truncate(pi_estimate, int(D)-1)


            pi_val_to_match = truncate(math.pi, int(D)-1)
            total_time = sum(elapsed_time)


            if float(pi_val_to_match) == float(truncated_pi_estimate):#remove + 1

                db.collection("miriam_cloud").add(
                    {"cost":total_time,
                    "d":D,
                    "pi_estimate":pi_estimate,
                    "q":Q,
                    "r":R,
                    "s":S}
                )
                break

            else:

                max_tries = max_tries -1


    elif service == "ec2":
        print("EC2")

    print("results: ",incircle_shot)
    return render_template("results.html",pi_estimations=pi_estimations,res=incircle_shot,incircle=incircle,shot=S,pi_estimate=pi_estimate)


@app.route("/<srvce>/<R>",methods = ["POST","GET"])
def lastPage(srvce, R):# function for the last page

    if request.method == "POST":
        S = request.form["number_of_shots"]
        Q = request.form["reporting_rate"]
        D = request.form["matching_digits"]


        return redirect(url_for("results",service=srvce,R=int(R),D=int(D),Q=int(Q),S=int(S)))

    else:
        return render_template("getRDQS.html")


@app.route("/history")
def history(): # function which output the values on history
    values = []
    my_runs = db.collection("miriam_cloud").get()
    for item in my_runs:

        values.append(item.to_dict())


    return render_template("history.html",items=values)





if __name__ == "__main__":

    app.run(debug=True)
