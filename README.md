아주 간단한 Docker Remote Driver(https://github.com/docker/libnetwork/blob/master/docs/remote.md)

> remote network driver는 docker의 experimental 기능을 사용하므로 해당 패키지가 필요함
> https://github.com/docker/docker/tree/master/experimental#install-docker-experimental

docker plugin 설정 

    # cat /etc/docker/plugin/test.spec
    http://localhost:8888

network create

    docker network create -d test test-network

docker run에서... --publish-service 옵션으로 container 실행

    docker run -d --publish-service service1.test-network --name test1 ubuntu sleep 36400
    docker run -d --publish-service service2.test-network --name test2 ubuntu sleep 36400

