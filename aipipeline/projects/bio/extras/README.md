EXPD data metadata grabber. Courtesy B.Schlining.

# Build

```shell
docker build -t get-expd-data .
```

# Run

```shell
docker run -it --rm get-expd-data Ventana 2017-09-12T17:00:15Z
```

# Help

java -jar get-expd-data.jar

Missing required parameters: '<rov>', '<timeString>'
Usage: get-data [-hV] <rov> <timeString>
Get nav + ctd from the database
      <rov>          The ROV name
      <timeString>   The start time. An ISO-8601 date-time string, e.g.
                       2020-01-01T12:00:00Z
  -h, --help         Show this help message and exit.
  -V, --version      Print version information and exit.


# When data is found it returns the following JSON

java -jar get-expd-data.jar Ventana 2017-09-12T17:00:15Z

{"rov": "Ventana","requestedTime": "2017-09-12T17:00:15Z","actualTime": "2017-09-12T17:00:15Z","latitude": 36.700819,"longitude": -122.049744,"depthMeters": 449.65564,"pressureDbar": 453.49,"temperature": 6.897,"salinity": 34.215,"oxygen": 0.661,"ligthTransmission": 81.99}


# When no data exists it returns an error message 

java -jar get-expd-data.jar Ventana 2027-09-12T17:00:15Z

{"error": "No dive found for Ventana at 2027-09-12T17:00:15Z"}