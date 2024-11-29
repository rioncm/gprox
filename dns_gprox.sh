#!/usr/bin/env sh
# shellcheck disable=SC2034
dns_gprox_info='Custom API for integrating with the GPROX DNS proxy for Google Cloud DNS.
Domains: blueplatypus.com
Site: github.com/rioncm/gprox-dns
Options:
 GPROX_ENDPOINT GPROX API Endpoint.
Issues: github.com/rioncm/gprox-dns
Author: Rion Morgenstern <rioncm@gmail.com>
'

########  Public functions #####################

# Usage: dns_gprox_add _acme-challenge.domain.com "challenge-token"
dns_gprox_add() {
  fulldomain=$1
  txtvalue=$2

  _info "Using GPROX to add TXT record"
  _debug fulldomain "$fulldomain"
  _debug txtvalue "$txtvalue"

  # Ensure GPROX_ENDPOINT is set
  GPROX_ENDPOINT="${GPROX_ENDPOINT:-$(_readaccountconf_mutable GPROX_ENDPOINT)}"
  GPROX_API_KEY="${GPROX_API_KEY:-$(_readaccountconf_mutable GPROX_API_KEY)}"
  if [ -z "$GPROX_ENDPOINT" ]; then
    _err "GPROX_ENDPOINT is not set for first time use export GPROX_ENDPOINT='your_api_endpoint'"
    return 1
  fi
if [ -z "$GPROX_API_KEY" ]; then
    _err "GPROX_API_KEY is not set for first time use export GPROX_API_KEY='your_api_key'"
    return 1
  fi

  # Save the endpoint to the account conf file
  _saveaccountconf_mutable GPROX_ENDPOINT "$GPROX_ENDPOINT"
  _saveaccountconf_mutable GPROX_API_KEY "$GPROX_API_KEY"

  # Prepare JSON payload
  payload="{\"fqdn\":\"$fulldomain\",\"value\":\"$txtvalue\",\"api_key\":\"$GPROX_API_KEY\"}"
  _debug payload "$payload"

  export _H1="Content-Type: application/json"

  # Send the request
  response="$(_post "$payload" "$GPROX_ENDPOINT/v1/dns/add")"
  _debug response "$response"

  # Check the response for success
  if _contains "$response" '"status":"success"'; then
    _info "TXT record added successfully"
    return 0
  else
    _err "Failed to add TXT record: $response"
    return 1
  fi
}

# Usage: dns_gprox_rm _acme-challenge.domain.com "challenge-token"
dns_gprox_rm() {
  fulldomain=$1
  txtvalue=$2

  _info "Using GPROX to remove TXT record"
  _debug fulldomain "$fulldomain"
  _debug txtvalue "$txtvalue"

    # Ensure GPROX_ENDPOINT is set
  GPROX_ENDPOINT="${GPROX_ENDPOINT:-$(_readaccountconf_mutable GPROX_ENDPOINT)}"
  GPROX_API_KEY="${GPROX_API_KEY:-$(_readaccountconf_mutable GPROX_API_KEY)}"
  if [ -z "$GPROX_ENDPOINT" ]; then
    _err "GPROX_ENDPOINT is not set for first time use export GPROX_ENDPOINT='your_api_endpoint'"
    return 1
  fi
if [ -z "$GPROX_API_KEY" ]; then
    _err "GPROX_API_KEY is not set for first time use export GPROX_API_KEY='your_api_key'"
    return 1
  fi

  # Prepare JSON payload
  payload="{\"fqdn\":\"$fulldomain\",\"value\":\"$txtvalue\",\"api_key\":\"$GPROX_API_KEY\"}"
  _debug payload "$payload"

  export _H1="Content-Type: application/json"

  # Send the request
  response="$(_post "$payload" "$GPROX_ENDPOINT/v1/dns/remove")"
  _debug response "$response"

  # Check the response for success
  if _contains "$response" '"status":"success"'; then
    _info "TXT record removed successfully"
    return 0
  else
    _err "Failed to remove TXT record: $response"
    return 1
  fi
}

####################  Private functions below ##################################