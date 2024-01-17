from fastapi_cprofile.profiler import CProfileMiddleware
app = FastAPI()
app.add_middleware(CProfileMiddleware, enable=True, server_app = app, filename='/tmp/output.pstats', strip_dirs = False, sort_by='cumulative'


pip install gprof2dot
gprof2dot -f pstats output.pstats | dot -Tpng -o output.png

