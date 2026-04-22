FROM golang:1.17.3

RUN git config --global http.sslverify false
COPY . /go/src/github.com/harlow/go-micro-services
WORKDIR /go/src/github.com/harlow/go-micro-services
RUN go get gopkg.in/mgo.v2
RUN go get github.com/bradfitz/gomemcache/memcache
RUN go get github.com/google/uuid
RUN go mod init
# Newer zerolog releases import the stdlib slog package, which is unavailable
# in the legacy Go toolchain used by this image.
RUN go get github.com/rs/zerolog@v1.31.0
RUN go mod vendor
# use local modified github.com/hailocab/go-geoindex instead of upstream one
COPY ./vendor/github.com/hailocab/go-geoindex /go/src/github.com/harlow/go-micro-services/vendor/github.com/hailocab/go-geoindex
RUN go install -ldflags="-s -w" ./cmd/...
