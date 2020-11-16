""" Wrapper script for awscli which handles Okta auth """
# pylint: disable=C0325,R0913,R0914
import os
from subprocess import call
import logging
import click
from oktaawscli.version import __version__
from oktaawscli.okta_auth import OktaAuth
from oktaawscli.okta_auth_config import OktaAuthConfig
from oktaawscli.aws_auth import AwsAuth

def get_credentials(aws_auth, okta_profile, profile,
                    verbose, logger, totp_token, cache, assertion, assertion_from_file, full, prefix, postfix):
    """ Gets credentials from Okta """

    if assertion_from_file is not None:
        f = open(assertion_from_file, 'r', encoding='UTF-8')
        assertion = f.read()
        f.close()

    
    if full:
        roles = aws_auth.full_choose_aws_role(assertion)
        for role in roles:
            p = role.role_arn.split('/')
            if prefix is not None and not p[1].startswith(prefix):
                continue
            if postfix is not None and not p[1].endswith(postfix):
                continue
            principal_arn, role_arn = role

            try:
                sts_token = aws_auth.get_sts_token(
                    role_arn,
                    principal_arn,
                    assertion,
                    duration=43200,
                    logger=logger
                )
                access_key_id = sts_token['AccessKeyId']
                secret_access_key = sts_token['SecretAccessKey']
                session_token = sts_token['SessionToken']
                session_token_expiry = sts_token['Expiration']
                logger.info("Session token expires on: %s" % session_token_expiry)
                aws_auth.write_sts_token(p[1], access_key_id,
                                        secret_access_key, session_token)
                print("role %s is set" % p[1])
            except Exception as e:
                print("role %s is not set yet or saml timeout" % p[1])
                pass
    else:
        role = aws_auth.choose_aws_role(assertion)
        principal_arn, role_arn = role

        sts_token = aws_auth.get_sts_token(
            role_arn,
            principal_arn,
            assertion,
            duration=43200,
            logger=logger
        )
        access_key_id = sts_token['AccessKeyId']
        secret_access_key = sts_token['SecretAccessKey']
        session_token = sts_token['SessionToken']
        session_token_expiry = sts_token['Expiration']
        logger.info("Session token expires on: %s" % session_token_expiry)
        if not profile:
            exports = console_output(access_key_id, secret_access_key,
                                    session_token, verbose)
            if cache:
                cache = open("%s/.okta-credentials.cache" %
                            (os.path.expanduser('~'),), 'w')
                cache.write(exports)
                cache.close()
            exit(0)
        else:
            aws_auth.write_sts_token(profile, access_key_id,
                                    secret_access_key, session_token)



def console_output(access_key_id, secret_access_key, session_token, verbose):
    """ Outputs STS credentials to console """
    if verbose:
        print("Use these to set your environment variables:")
    exports = "\n".join([
        "export AWS_ACCESS_KEY_ID=%s" % access_key_id,
        "export AWS_SECRET_ACCESS_KEY=%s" % secret_access_key,
        "export AWS_SESSION_TOKEN=%s" % session_token
    ])
    print(exports)

    return exports


# pylint: disable=R0913
@click.command()
@click.option('-v', '--verbose', is_flag=True, help='Enables verbose mode')
@click.option('-V', '--version', is_flag=True,
              help='Outputs version number and exits')
@click.option('-d', '--debug', is_flag=True, help='Enables debug mode')
@click.option('-f', '--force', is_flag=True, help='Forces new STS credentials. \
Skips STS credentials validation.')
@click.option('--okta-profile', help="Name of the profile to use in .okta-aws. \
If none is provided, then the default profile will be used.\n")
@click.option('--profile', help="Name of the profile to store temporary \
credentials in ~/.aws/credentials. If profile doesn't exist, it will be \
created. If omitted, credentials will output to console.\n")
@click.option('-c', '--cache', is_flag=True, help='Cache the default profile credentials \
to ~/.okta-credentials.cache\n')
@click.option('-t', '--token', help='TOTP token from your authenticator app')
@click.option('-a', '--assertion', help='assertion of okta')

@click.option('--assertion-from-file', help='assertion from file of okta')
@click.option('--full', is_flag=True, help='full roles of okta')
@click.option('--prefix', help='full prefix roles of okta')
@click.option('--postfix', help='full postfix roles of okta')
@click.argument('awscli_args', nargs=-1, type=click.UNPROCESSED)
def main(okta_profile, profile, verbose, version,
         debug, force, cache, awscli_args, token, assertion, assertion_from_file, full, prefix, postfix):
    """ Authenticate to awscli using Okta """
    if version:
        print(__version__)
        exit(0)
    # Set up logging
    logger = logging.getLogger('okta-awscli')
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setLevel(logging.WARN)
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    if verbose:
        handler.setLevel(logging.INFO)
    if debug:
        handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    if not okta_profile:
        okta_profile = "default"
    aws_auth = AwsAuth(profile, okta_profile, verbose, logger)
    if not aws_auth.check_sts_token(profile) or force:
        if force and profile:
            logger.info("Force option selected, \
                getting new credentials anyway.")
        elif force:
            logger.info("Force option selected, but no profile provided. \
                Option has no effect.")
        get_credentials(
            aws_auth, okta_profile, profile, verbose, logger, token, cache, assertion, assertion_from_file, full, prefix, postfix
        )

    if awscli_args:
        cmdline = ['aws', '--profile', profile] + list(awscli_args)
        logger.info('Invoking: %s', ' '.join(cmdline))
        call(cmdline)


if __name__ == "__main__":
    # pylint: disable=E1120
    main()
    # pylint: enable=E1120
