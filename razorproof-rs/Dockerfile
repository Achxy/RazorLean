# Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
# SPDX-License-Identifier: MIT
# Licensed under the MIT License. See LICENSE in the repository root.

FROM rust:1.96.0-bookworm AS builder
WORKDIR /src
COPY . .
RUN cargo build --locked --release -p razorproof-cli

FROM debian:bookworm-slim AS runtime
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --system --uid 10001 --home-dir /nonexistent --shell /usr/sbin/nologin razorproof \
    && install -d -o razorproof -g razorproof /data
COPY --from=builder /src/target/release/razorproof /usr/local/bin/razorproof
USER 10001:10001
WORKDIR /data
EXPOSE 8787
ENTRYPOINT ["/usr/local/bin/razorproof"]
CMD ["serve"]
