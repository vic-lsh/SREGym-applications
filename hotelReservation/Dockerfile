FROM golang:1.17.3

RUN git config --global http.sslverify false
COPY . /go/src/github.com/harlow/go-micro-services
WORKDIR /go/src/github.com/harlow/go-micro-services
RUN go get gopkg.in/mgo.v2
RUN go get github.com/bradfitz/gomemcache/memcache
RUN go get github.com/google/uuid
RUN go mod init
# go mod vendor otherwise resolves the newest zerolog, which needs Go >= 1.21 (log/slog).
RUN go mod edit -require=github.com/rs/zerolog@v1.20.0
RUN go mod vendor
# use local modified github.com/hailocab/go-geoindex instead of upstream one
COPY ./vendor/github.com/hailocab/go-geoindex /go/src/github.com/harlow/go-micro-services/vendor/github.com/hailocab/go-geoindex
RUN go install -ldflags="-s -w" ./cmd/...
