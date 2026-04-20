import pulumi
import pulumi_akamai as akamai
import json

# 1. Initialize Pulumi Config
config = pulumi.Config()

contract_id   = config.require("contractId")
group_id      = config.require("groupId")
product_id    = config.require("productId")
prop_name     = config.require("propertyName")
origin_host   = config.require("originHostname")
edge_host     = config.require("edgeHostname")
prop_hostname = config.require("propertyHostname")
rule_format   = config.require("ruleFormat")
cache_ttl     = config.require("cacheTtl")
ip_behavior   = config.require("ipBehavior")
edge_ttl      = config.get_int("edgeHostnameTtl") or 300
act_network   = config.require("activateNetwork")
auto_ack      = config.get_bool("autoAcknowledgeRuleWarnings") or True
emails        = config.get_object("notificationEmails") or ["admin@example.com"]

# 2. CP Code & 3. Edge Hostname (Pulumi already tracks these in state)
cp_code = akamai.CpCode("amdCpCode",
    name=f"{prop_name}-cp".replace("_", "-"), 
    contract_id=contract_id,
    group_id=group_id,
    product_id=product_id
)

edge_hostname_res = akamai.EdgeHostName("sharedCertEdgeHostname",
    contract_id=contract_id,
    group_id=group_id,
    product_id=product_id,
    edge_hostname=edge_host,
    ip_behavior=ip_behavior,
    ttl=edge_ttl
)

# 4. Barebones Rule Tree with Schema-Valid Enums
def generate_rules(cp_code_output):
    numeric_id = int(cp_code_output.split('_')[-1])
    rules_dict = {
        "rules": {
            "name": "default",
            "behaviors": [
                {
                    "name": "origin",
                    "options": {
                        "hostname": origin_host,
                        "forwardHostHeader": "ORIGIN_HOSTNAME",
                        "cacheKeyHostname": "ORIGIN_HOSTNAME",
                        "compress": True,
                        "originType": "CUSTOMER"
                    }
                },
                {
                    "name": "cpCode",
                    "options": { "value": { "id": numeric_id } }
                },
                {
                    "name": "caching",
                    "options": {
                        "behavior": "MAX_AGE",
                        "mustRevalidate": False,
                        "ttl": cache_ttl
                    }
                },
                {
                    "name": "originCharacteristics",
                    "options": {
                        "country": "UNKNOWN",
                        "authenticationMethod": "AUTOMATIC"
                    }
                },
                {
                    "name": "clientCharacteristics",
                    "options": {
                        "country": "NORTH_AMERICA"
                    }
                },
                {
                    "name": "segmentedMediaOptimization",
                    "options": {
                        "behavior": "ON_DEMAND",
                        "enableUplinkQuic": False
                    }
                },
                {
                    "name": "contentCharacteristicsAMD",
                    "options": {
                        "contentType": "HD",
                        "catalogSize": "UNKNOWN",
                        "popularity": "UNKNOWN"
                    }
                }
            ],
            "children": [],
            # MANDATORY: False for Standard TLS / Shared Cert
            "options": { "is_secure": False } 
        }
    }
    return json.dumps(rules_dict)

# 5. Create the AMD Property
amd_property = akamai.Property("amdConfig",
    name=prop_name,
    contract_id=contract_id,
    group_id=group_id,
    product_id=product_id,
    rule_format=rule_format,
    hostnames=[akamai.PropertyHostnameArgs(
        cname_from=prop_hostname,
        cname_to=edge_hostname_res.edge_hostname,
        # FIX: "CPS_MANAGED" is the correct value for pre-existing Shared Certs
        cert_provisioning_type="CPS_MANAGED", 
    )],
    rules=cp_code.id.apply(generate_rules)
)

# 6. Deploy to Network
activation = akamai.PropertyActivation("activateAmd",
    property_id=amd_property.id,
    contacts=emails,
    version=amd_property.latest_version,
    network=act_network,
    # This ignores the 'Quick Retry' warning and lets the deployment finish
    auto_acknowledge_rule_warnings=auto_ack,
    note="Managed by Pulumi - Final Shared Cert Activation Fix"
)

# Exports
pulumi.export("property_id", amd_property.id)
pulumi.export("edge_hostname_assigned", edge_hostname_res.edge_hostname)