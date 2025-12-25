import pulumi

import resources

pulumi.log.info("Loaded resources module")
for resource_name in resources.__all__:
    pulumi.log.info(f"- {resource_name}")
