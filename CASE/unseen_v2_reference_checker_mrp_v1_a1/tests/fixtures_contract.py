"""Artificial build/authorization metadata for validation tests, never executed.

Native source copies match the frozen kernel. Binary/library/compiler files are
labelled inert bytes. A passing binding test validates schema/closure handling,
not a native build, human declaration, execution permission or physical result.
"""
from pathlib import Path
import json
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'analysis'))
from evidence import sha

CASE=Path(__file__).resolve().parents[1]
OLD=CASE.parent/'unseen_v2_reference_v1'

class ContractFixture:
    def __init__(self,root):
        self.root=Path(root).resolve();self.build=self.root/'SYNTHETIC_BUILD_NOT_EXECUTABLE';self.build.mkdir()
        self.run=self.root/'SYNTHETIC_RAW_P';self.run.mkdir()
        self.sources=[]
        for name in ['urv_reference.cpp','mass_stats.h']:
            p=self.build/name;p.write_bytes((OLD/'src'/name).read_bytes());self.sources.append(p)
        self.binary=self.file('NATIVE_PLACEHOLDER_NOT_EXECUTABLE','SYNTHETIC inert bytes, no build or run\n')
        self.recipe=self.file('Makefile','SYNTHETIC recipe fixture\n')
        self.compiler=self.file('COMPILER_PLACEHOLDER_NOT_EXECUTABLE','SYNTHETIC inert compiler\n')
        self.header=self.file('dependency.h','SYNTHETIC include file\n')
        self.dep=self.file('dependency.d','object.o: '+' '.join(str(p) for p in [*self.sources,self.header])+'\n')
        self.static=[self.file('lib'+n+'.a','SYNTHETIC static bytes\n') for n in ['olbcore','z','tinyxml2']]
        self.runtime=self.file('libsynthetic.so','SYNTHETIC runtime bytes\n')
        self.ldd=self.file('ldd.txt','libsynthetic.so => '+str(self.runtime)+' (0x000000)\n')
        self.cfg=self.run/'run_config.txt'
        self.cfg.write_text('mode=steady\nrun_id=SYNTHETIC_S0_P\noutput_directory='+str(self.run)+
            '\ndirection=P\ndx_nm=5\nh_nm=75\nd_nm=100\nw_nm=120\nperiod_nm=240\nLy_nm=240\nnu_m2_s=1e-6\nacceleration_m_s2=100000\nwindow_tstar=.75\nmax_time_H_diffusion=8\nframe_tstar=0,0.01,0.02,0.05,0.1,0.2,0.5,1,2,4,8\n')
        self.envpath=self.build/'build_environment.json'
        self.env=dict(compile_exit_code=0,preparation_only_build=False,
            fixture_label='SYNTHETIC_BUILD_CAPTURE_NO_BUILD_OCCURRED',
            binary_path=str(self.binary),binary_sha256=sha(self.binary),
            build_recipe_path=str(self.recipe),build_recipe_sha256=sha(self.recipe),
            compile_command='compiler -DURV_PREPARATION_ONLY=0 -c urv_reference.cpp',
            native_sources_sha256={str(p):sha(p) for p in self.sources},
            dependency_file_path=str(self.dep),compile_working_directory=str(self.build),
            dependency_sha256={str(p):sha(p) for p in [*self.sources,self.header]},
            link_library_sha256={str(p):sha(p) for p in self.static},
            dynamic_library_sha256={str(self.runtime):sha(self.runtime)},
            compiler_executable=str(self.compiler),compiler_sha256=sha(self.compiler))
        self.path=self.root/'SYNTHETIC_RELEASE_NOT_USER_AUTHORIZATION.json'
        self.document=dict(protocol_id='URV-v1',schema_version='URV-EXEC-1.1',
            simulation_authorized=True,preparation_only_build=False,
            author_external_data_history_confirmation='CONFIRMED',
            fixture_label='SYNTHETIC_FLAGS_ONLY_NO_AUTHOR_CONFIRMATION_OR_EXECUTION_AUTHORITY',
            stage='S0_REGRESSION',approved_run_ids=['SYNTHETIC_S0_P'],
            approved_runs=[dict(run_id='SYNTHETIC_S0_P',planned_case_id='URV1_H75_P_dx5_a100000',
                run_config_path=str(self.cfg),run_config_sha256=sha(self.cfg),output_directory=str(self.run))],
            provenance=dict(native_binary=str(self.binary),native_sources=[str(p) for p in self.sources],
                build_recipe=str(self.recipe),build_environment=str(self.envpath),dependency_file=str(self.dep),ldd_record=str(self.ldd)))
        self.refresh()

    def file(self,name,text):
        p=self.build/name;p.write_text(text);return p

    def refresh(self):
        self.envpath.write_text(json.dumps(self.env))
        files=[*self.build.iterdir(),self.cfg,*CASE.joinpath('analysis').glob('*.py'),*CASE.joinpath('common').glob('*')]
        self.document['inputs_sha256']={str(p.resolve()):sha(p) for p in files if p.is_file()}
        self.path.write_text(json.dumps(self.document))
        return sha(self.path)

    def rewrite(self):
        self.path.write_text(json.dumps(self.document));return sha(self.path)
