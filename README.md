# okta-awscli - Retrieve AWS credentials from Okta

Master branch: [![Build Status - master](https://travis-ci.org/jmhale/okta-awscli.svg?branch=master)](https://travis-ci.org/jmhale/okta-awscli)

Develop branch: [![Build Status - develop](https://travis-ci.org/jmhale/okta-awscli.svg?branch=develop)](https://travis-ci.org/jmhale/okta-awscli)

Authenticates a user against Okta and then uses the resulting SAML assertion to retrieve temporary STS credentials from AWS.

This project is largely inspired by https://github.com/nimbusscale/okta_aws_login, but instead uses a purely API-driven approach, instead of parsing HTML during the authentication phase.

Parsing the HTML is still required to get the SAML assertion, after authentication is complete. However, since we only need to look for the SAML assertion in a single, predictable tag, `<input name="SAMLResponse"...`, the results are a lot more stable across any changes that Okta may make to their interface.


## Installation

- `pip install okta-awscli`
  - To install with U2F support (Yubikey): `pip install "okta-awscli[U2F]"`
- Configure okta-awscli via the `~/.okta-aws` file with the following parameters:

```
[default]
base-url = <your_okta_org>.okta.com
app-link = <app_link_from_okta> # Found in Okta's configuration for your AWS account.
```

## Supported Features

- Tenant wide MFA support
- Per-application MFA support (added in version 0.4.0)
- Okta Verify [Play Store](https://play.google.com/store/apps/details?id=com.okta.android.auth) | [App Store](https://itunes.apple.com/us/app/okta-verify/id490179405)
- Okta Verify Push Support
- Google Authenticator [Play Store](https://play.google.com/store/apps/details?id=com.google.android.apps.authenticator2) | [App Store](https://itunes.apple.com/us/app/google-authenticator/id388497605)
- YubiKey (Requires library python-u2flib-host)  [HomePage](https://www.yubico.com/)

## Usage

`okta-awscli --profile <aws_profile> <awscli action> <awscli arguments>`
- Follow the prompts to enter MFA information (if required) and choose your AWS app and IAM role.
- Subsequent executions will first check if the STS credentials are still valid and skip Okta authentication if so.
- Multiple Okta profiles are supported, but if none are specified, then `default` will be used.
- Selections for AWS App and AWS Role are saved to the `~/.okta-aws` file. Removing the `app-link` and `role` fields will enable the prompts for these selections.

### Example

`okta-awscli --profile my-aws-account iam list-users`

If no awscli commands are provided, then okta-awscli will simply output STS credentials to your credentials file, or console, depending on how `--profile` is set.

Optional flags:
- `--profile` Sets your temporary credentials to a profile in `.aws/credentials`. If omitted, credentials will output to console.
- `--force` Ignores result of STS credentials validation and gets new credentials from AWS. Used in conjunction with `--profile`.
- `--verbose` More verbose output.
- `--debug` Very verbose output. Useful for debugging.
- `--cache` Cache the acquired credentials to ~/.okta-credentials.cache (only if --profile is unspecified)
- `--okta-profile` Use a Okta profile, other than `default` in `.okta-aws`. Useful for multiple Okta tenants.
- `--token` or `-t` Pass in the TOTP token from your authenticator

## Run from docker container
This process is taken from gimme-aws-creds and adapted

### Build the image 
```
docker build -t okta-awscli .

```
### Run the image with the command

```
docker run -it --rm -v ~/.aws/credentials:/root/.aws/credentials -v ~/.okta-aws:/root/.okta-aws --profile default okta-awscli iam list-users
```

### if you want to type less you can create an alias

```
alias okta-awscli='docker run -it --rm -v ~/.aws:/root/.aws -v ~/.okta-aws:/root/.okta-aws okta-awscli'
```

and just type 
```
okta-awscli
```

you can add this to you .bashrc 
```
source <PATH TO GIT REPO>/set-alias.bash
```

