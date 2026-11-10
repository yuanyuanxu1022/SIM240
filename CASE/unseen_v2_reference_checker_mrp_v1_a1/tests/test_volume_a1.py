"""A1 software arithmetic and actual build-binding checks; never solves."""
from pathlib import Path
import ctypes,json,math,sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'analysis'))
from mass_capture import bits
from contracts import verify_provenance
from evidence import sha
import test_mrp as mrptests
NATIVE,LIB,CASE=mrptests.NATIVE,mrptests.LIB,mrptests.CASE

LIB.mrp_volume_prefixes.argtypes=[ctypes.c_double,ctypes.POINTER(ctypes.c_double),ctypes.c_ulong]
LIB.mrp_volume_prefixes.restype=None

class VolumeA1Tests(unittest.TestCase):
    def test_all_57600_volume_prefixes_exact(self):
        count=57600;dx=5e-9;actual=(ctypes.c_double*count)()
        LIB.mrp_volume_prefixes(dx,actual,count)
        expected=0.;term=(dx*dx)*dx
        for i in range(count):
            expected=expected+term
            self.assertEqual(bits(actual[i]),bits(expected),f'spatial ordinal {i}')

    def test_original_fused_path_is_discriminated(self):
        dx=5e-9;fused=split=0.;different=0
        for i in range(57600):
            fused=math.fma(dx*dx,dx,fused);split=split+(dx*dx)*dx
            different+=bits(fused)!=bits(split)
        self.assertEqual(different,196)
        self.assertEqual(bits(fused),bits(split))

    def test_fixture_uses_exact_adopted_native_expression(self):
        block='      const volatile T roundedCellVolume = dx * dx * dx;\n      value.volume += roundedCellVolume;'
        self.assertEqual((NATIVE/'src/urv_reference.cpp').read_text().count(block),1)
        self.assertEqual((CASE/'tests/mrp_arithmetic_fixture.cpp').read_text().count(block),1)

    def test_A1_actual_build_provenance(self):
        # Binding check only: no simulation_authorized flags or run records.
        helper=mrptests.MRPTests();bound,_=helper.revision_bound()
        environment=json.loads((NATIVE/'evidence/build_environment.json').read_text())
        build=[NATIVE/'src/Makefile',NATIVE/'build/urv_reference',NATIVE/'build/urv_reference.d',
               NATIVE/'evidence/build_environment.json',NATIVE/'evidence/ldd.txt']
        for p in build:bound['inputs_sha256'][str(p)]=sha(p)
        for folder in ['analysis','common']:
            for p in (CASE/folder).iterdir():
                if p.is_file():bound['inputs_sha256'][str(p)]=sha(p)
        for key in ['dependency_sha256','link_library_sha256','dynamic_library_sha256']:
            bound['inputs_sha256'].update(environment[key])
        bound['inputs_sha256'][environment['compiler_executable']]=environment['compiler_sha256']
        bound['schema_version']='URV-EXEC-1.1'
        bound['provenance'].update(native_binary=str(NATIVE/'build/urv_reference'),
            build_recipe=str(NATIVE/'src/Makefile'),build_environment=str(NATIVE/'evidence/build_environment.json'),
            dependency_file=str(NATIVE/'build/urv_reference.d'),ldd_record=str(NATIVE/'evidence/ldd.txt'))
        verify_provenance(bound)

if __name__=='__main__':unittest.main()
