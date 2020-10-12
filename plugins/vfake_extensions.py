import ipaddress
import re
from contextlib import suppress
from string import ascii_uppercase, digits

from visidata import BaseSheet, asyncthread, vd

from faker.providers import BaseProvider
from faker_cloud import AmazonWebServicesProvider


def _isNullFunc():
    '''
    isNullFunc is available as a sheet property in newer VisiData releases, but
    was previously a function in the "visidata" module. Try to use the sheet
    property, but fall back to support earlier versions.
    '''
    try:
        return vd.sheet.isNullFunc()
    except AttributeError:
        import visidata

        return visidata.isNullFunc()


class VdCustomProvider(BaseProvider):
    '''Bonus faketypes for use with vfake.'''

    def account_id(self):
        return "123456789012"

    def ws_bundle_id(self):
        return self.hexify(f"wsb-{'^' * 9}")

    def ws_computer_name(self):
        return self.lexify(f"EC2AMAZ-{'?' * 7}", ascii_uppercase + digits)

    def directory_id(self):
        return self.hexify(f"d-{'^' * 10}")

    def subnet_id(self):
        return self.hexify(f"subnet-{'^' * 8}")

    def workspace_id(self):
        return self.hexify(f"ws-{'^' * 9}")

    def eni_id(self):
        return self.hexify(f"eni-{'^' * 17}")


try:
    import plugins.vfake

    vd.options.vfake_extra_providers = [AmazonWebServicesProvider, VdCustomProvider]
except Exception as err:
    vd.warning(f'Error importing vfake dependency for vfake_extensions: {err}')

### Helper condition checker functions for autofake


def match(pat):
    r = re.compile(pat)

    def wrapper(val, _):
        return re.match(r, val)

    return wrapper


def is_public_ip(addr, _):
    try:
        ipv4 = ipaddress.IPv4Address(addr)
        return ipv4.is_global
    except ipaddress.AddressValueError:
        return False


def is_private_ip(addr, _):
    try:
        ipv4 = ipaddress.IPv4Address(addr)
        return ipv4.is_private
    except ipaddress.AddressValueError:
        return False


def is_port(val, colname):
    try:
        return 0 <= int(val) <= 65535 and 'port' in colname.casefold()
    except ValueError:
        return False


# Guess a faker generator function for a column and value based
# on a matcher function. First match wins.

faketype_mapping = {
    match(r'^i-'): 'instance_id',
    match(r'^vpc-'): 'vpc_id',
    match(r'^eni-'): 'eni_id',
    match(r'^ws-'): 'workspace_id',
    match(r'^subnet-'): 'subnet_id',
    match(r'^sg-'): 'security_group_id',
    match(r'^d-'): 'directory_id',
    match(r'^wsb-'): 'ws_bundle_id',
    match(r'^\d{12}$'): 'account_id',
    is_private_ip: 'ipv4_private',
    is_public_ip: 'ipv4_public',
    is_port: 'port_number',
}


@asyncthread
@BaseSheet.api
def autofake(sheet, cols, rows):
    '''
    Try to guess an appropriate vfake faketype for a given column and row set.
    If we find a match, run with it. NO REGERTS.
    '''

    isNull = _isNullFunc()
    for col in cols:
        faketype = None
        with suppress(StopIteration):
            next(r for r in rows if not isNull(hint := col.getValue(r)))
            faketype = next(
                v for k, v in faketype_mapping.items() if k(str(hint), col.name)
            )
        if not faketype:
            vd.warning(f'Could not detect a fake type for column {col.name}')
            continue
        vd.status(f'Detected fake type {faketype} for column {col.name}')
        vd.addUndoSetValues([col], rows)
        col.setValuesFromFaker(faketype, rows)


BaseSheet.bindkey("zf", "setcol-fake")
BaseSheet.addCommand(
    "gzf",
    'setcol-fake-all',
    'cursorCol.setValuesFromFaker(vd.input("faketype: ", type="faketype"), rows)',
)
BaseSheet.addCommand('z^F', 'setcol-autofake', f'sheet.autofake([cursorCol], rows)')
BaseSheet.addCommand('gz^F', 'setcols-autofake', f'sheet.autofake(columns, rows)')
