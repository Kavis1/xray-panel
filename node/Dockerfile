FROM golang:1.21-alpine AS builder

WORKDIR /build

RUN apk add --no-cache git

COPY go.mod go.sum ./
RUN go mod download

COPY . .

RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o node cmd/main.go

FROM alpine:latest

RUN apk --no-cache add ca-certificates wget unzip

# Install Xray-core
RUN wget -O /tmp/xray.zip https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip && \
    unzip /tmp/xray.zip -d /usr/local/bin && \
    chmod +x /usr/local/bin/xray && \
    rm /tmp/xray.zip

WORKDIR /app

COPY --from=builder /build/node .

ENV SERVICE_PORT=50051
ENV SERVICE_PROTOCOL=grpc
ENV NODE_HOST=0.0.0.0
ENV XRAY_EXECUTABLE_PATH=/usr/local/bin/xray
ENV XRAY_ASSETS_PATH=/usr/local/share/xray

EXPOSE 50051

CMD ["./node"]
