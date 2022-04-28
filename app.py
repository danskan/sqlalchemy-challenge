from flask import Flask, jsonify
import numpy as np
import datetime as dt
import pandas as pd
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

engine = create_engine("sqlite:///hawaii.sqlite")
Base = automap_base()
Base.prepare(engine, reflect=True)

measurement = Base.classes.measurement
station = Base.classes.station

app = Flask(__name__)

@app.route("/")
def home():
    return(
        f"<h2>Home Page</h2><br>"
        f"<h4>The Available Routes Are as Follows: </h4><br>"
        f"<h4>/api/v1.0/precipitation</h4><br>"
        f"<h4>/api/v1.0/stations</h4><br>"
        f"<h4>/api/v1.0/tobs</h4><br>"
        f"<h4>/api/v1.0/yyyy-mm-dd   <<-------Temps from the start date: yyyy-mm-dd</h4><br>"
        f"<h4>/api/v1.0/yyyy-mm-dd/yyyy-mm-dd <<------ Temps from start to end dates.</h4><br>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    session = Session(engine)
    selection = [measurement.date, measurement.prcp]
    precip_info = session.query(*selection)
    session.close()

    precipitation_list = []
    date_list = []
    for date, prcp in precip_info:
        precipitation_list.append(prcp)
        date_list.append(date)
    zipped = zip(date_list, precipitation_list)
    precip_dict = dict(zipped)
    return jsonify(precip_dict)

@app.route("/api/v1.0/stations")
def stations():
    session = Session(engine)
    selection = [station.station]
    stations_info = session.query(*selection)
    session.close()
    stations_list = []
    for s in stations_info:
        stations_list.append(s)
    return jsonify(stations_list)

@app.route("/api/v1.0/tobs")
def tobs():
    session = Session(engine)
    most_recent_date = session.query(measurement.date).order_by(measurement.date.desc()).first()
    one_year_ago = dt.datetime.strptime(most_recent_date[0],"%Y-%m-%d") - dt.timedelta(days=365)
    selection = [measurement.station, func.count(measurement.station)]
    active_stations = session.query(*selection).group_by(measurement.station).order_by(func.count(measurement.station).desc()).all()
    active_stations_df = pd.DataFrame(active_stations, columns = ['station', 'count'])
    max_count = active_stations_df['count'].max()
    most_active_station = active_stations_df[active_stations_df['count']==max_count]
    most_active_station_id = most_active_station['station'][0]
    selection = [measurement.station, measurement.date, measurement.tobs]
    most_active_station_temps = session.query(*selection).filter(measurement.date >= one_year_ago)
    most_active_station_temps_df = pd.DataFrame(most_active_station_temps, columns = ['station', 'date', 'temp'])
    final_df = most_active_station_temps_df[most_active_station_temps_df['station'] == most_active_station['station'][0]]
    final_df = final_df[['date', 'temp']]
    tobs_dict = dict(final_df.values)
    session.close()

    return jsonify(tobs_dict)

@app.route("/api/v1.0/<start>")
def given_start(start):
    session = Session(engine)
    selection = [func.max(measurement.tobs), func.min(measurement.tobs), func.avg(measurement.tobs)]
    prcp_and_dates = session.query(*selection).filter(measurement.date >= start).all()

    final_list = []
    temp_dict = {}
    for max, min, avg in prcp_and_dates:
        temp_dict['max'] = max
        temp_dict['min'] = min
        temp_dict['avg'] = avg
        final_list.append(temp_dict)
    session.close()

    return jsonify(final_list)

@app.route("/api/v1.0/<start>/<end>")
def start_end(start, end):
    session = Session(engine)
    selection = [func.max(measurement.tobs), func.min(measurement.tobs), func.avg(measurement.tobs)]
    precip_and_dates = session.query(*selection).filter(measurement.date >= start).filter(measurement.date <= end).all()
    final_list = []
    temp_dict = {}
    for max, min, avg in precip_and_dates:
        temp_dict['max'] = max
        temp_dict['min'] = min
        temp_dict['avg'] = avg
        final_list.append(temp_dict)
    
    session.close()

    return jsonify(final_list)

if __name__ == "__main__":
    app.run(debug=True)