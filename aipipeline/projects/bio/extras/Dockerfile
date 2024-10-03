FROM openjdk:11-jdk-slim
WORKDIR /app
COPY get-expd-data.jar /app/get-expd-data.jar
COPY run.sh /app/run.sh
RUN chmod +x run.sh
ENTRYPOINT ["./run.sh"]