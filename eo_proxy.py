from net.EOProxy import EOProxy

print("== Simple EOProxy Python v1.2.2 by Exile ==")

# Initialize EOProxy instance
eoproxy = EOProxy()

# Run the proxy with specified local and remote endpoints
eoproxy.run_proxy(
    '0.0.0.0', 8079,  # Local endpoint
    '23.158.72.18', 8078   # Remote endpoint
)
