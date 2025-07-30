docker build -t localmeteo .

docker rm --force localmeteo

docker run -d -p 80:80 -p 53:53 --name localmeteo localmeteo