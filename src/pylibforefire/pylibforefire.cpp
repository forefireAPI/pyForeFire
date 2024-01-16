#include "pylibforefire.h"

namespace py = pybind11;

using namespace std;
using namespace libforefire;
#include <iostream>

Command* pyxecutor;
Command::Session* session;
SimulationParameters* params;


PLibForeFire::PLibForeFire() {
	pyxecutor = new Command();
	session = &(pyxecutor->currentSession);
	params = session->params;
}

void PLibForeFire::createDomain( int id
		,  int year,  int month
		,  int day,  double t
		,  double lat,  double lon
		,  int mdimx,  double* meshx
		,  int mdimy,  double* meshy
		,  int mdimz,  double* zgrid
		,  double dt){


	/* Defining the Fire Domain */
		if (session->fd) delete session->fd;

		session->fd = new FireDomain(id, year, month, day, t, lat, lon
				, mdimx, meshx, mdimy, meshy, mdimz, dt);

		// pyxecutor->getDomain() = session->fd; // FIXME

		// A FireDomain has been created, the level is increased
		pyxecutor->increaseLevel();
		session->ff = session->fd->getDomainFront();
		// Defining the timetable of the events to be be in the domain
		if (session->tt) delete session->tt;
		session->tt = new TimeTable();
		// Associating this timetable to the domain
		session->fd->setTimeTable(session->tt);
		// Defining the simulator
		if (session->sim) delete session->sim;
		session->sim = new Simulator(session->tt, session->fd->outputs);


		session->outStrRep = new StringRepresentation(pyxecutor->getDomain());
		if ( SimulationParameters::GetInstance()->getInt("outputsUpdate") != 0 ){
			session->tt->insert(new FFEvent(session->outStrRep));
		}

		double deltaT = session->fd->getSecondsFromReferenceTime(year, month, day, t);

		pyxecutor->setReferenceTime(deltaT);
		pyxecutor->setStartTime(deltaT);
}

void PLibForeFire::addLayer(char *type, char* layername, char* keyname){

	pyxecutor->getDomain()->addLayer(string(type),string(layername),string(keyname));
}

void PLibForeFire::setInt(char* name, int val){
	string lname(name);
	params->setInt(lname,val);
}

int PLibForeFire::getInt(char* name ){
	string lname(name);
	return params->getInt(lname);
}

void PLibForeFire::setDouble(char* name, double val){
	string lname(name);
	params->setDouble(lname,val);
}

double PLibForeFire::getDouble(char* name ){
	string lname(name);
	return params->getDouble(lname);
}

void PLibForeFire::setString(char* name, char* val){
	string lname(name);
	string lval(val);
		params->setParameter(lname,val);
}

string PLibForeFire::getString(char *name)
{

	return params->getParameter(string(name));
}

string PLibForeFire::execute(char *command)
{
	ostringstream stringOut;
	pyxecutor->setOstringstream(&stringOut);
	string smsg(command);
	pyxecutor->ExecuteCommand(smsg);
	return stringOut.str();
}


void PLibForeFire::addScalarLayer(char *type, char *name, double x0 , double y0, double t0, double width , double height, double timespan, int nnx, int nny, int nnz, int nnl, py::array_t<double> values){

	FFPoint *p0 = new FFPoint(x0,y0,0);
	FFPoint *pe = new FFPoint(width,height,0);
	string lname(name);
	string ltype(type);

	size_t ni = nnx;
	size_t nj = nny;
	size_t nk = nnz;
	size_t nl = nnl;

 	pyxecutor->getDomain()->addScalarLayer(type, lname, x0, y0, t0, width, height, timespan, ni, nj, nk, nl, values.mutable_data());

}

void PLibForeFire::addIndexLayer(char *type, char *name, double x0 , double y0, double t0, double width , double height, double timespan, int nnx, int nny, int nnz, int nnl, py::array_t<int> values){
	FFPoint *p0 = new FFPoint(x0,y0,0);
	FFPoint *pe = new FFPoint(width,height,0);
	string lname(name);
	string ltype(type);

	size_t ni = nnx;
	size_t nj = nny;
	size_t nk = nnz;
	size_t nl = nnl;

 	pyxecutor->getDomain()->addIndexLayer(ltype, lname, x0, y0, t0, width, height, timespan, ni, nj, nk, nl, values.mutable_data());
}

py::array_t<double> PLibForeFire::getDoubleArray(char* name){
	double lTime = pyxecutor->getDomain()->getSimulationTime();

	return PLibForeFire::getDoubleArray(name, lTime);
}

py::array_t<double> PLibForeFire::getDoubleArray(char* name, double t){
	string lname(name);
	FluxLayer<double>* myFluxLayer = pyxecutor->getDomain()->getFluxLayer(lname);

		if ( myFluxLayer ){
			FFArray<double>* srcD;
			myFluxLayer->getMatrix(&srcD, t);
			double* data = srcD->getData();
			int nnx = srcD->getDim("x");
			int nny = srcD->getDim("y");
			int nnz = srcD->getDim("z");
			constexpr size_t stride_size = sizeof(double);
			py::array_t<double> arr = py::array_t<double>(
				{nnx, nny, nnz}, // shape
            	{nnz*nny*stride_size, nnz*stride_size, stride_size},
				data
			);
			return arr;
		}

	DataLayer<double>* myDataLayer = pyxecutor->getDomain()->getDataLayer(lname);

		if ( myDataLayer ){
			FFArray<double>* srcD;
			myDataLayer->getMatrix(&srcD, t);
			double* data = srcD->getData();
			int nnx = srcD->getDim("x");
			int nny = srcD->getDim("y");
			int nnz = srcD->getDim("z");
			constexpr size_t stride_size = sizeof(double);
			py::array_t<double> arr = py::array_t<double>(
				{nnx, nny, nnz}, // shape
            	{nnz*nny*stride_size, nnz*stride_size, stride_size},
				data
			);
			return arr;
		}

		double* data = NULL;
		py::array_t<double> arr = py::array_t<double>(
			{0, 0, 0}, // shape
			{8, 8, 8},
			data
		);
		return arr;
}

PYBIND11_MODULE(pyforefire, m) {
    m.doc() = "pybind11 pyforefire plugin"; // optional module docstring

    py::class_<PLibForeFire>(m, "ForeFire")
        .def(py::init())
		.def("createDomain", &PLibForeFire::createDomain)
        .def("addLayer", &PLibForeFire::addLayer)
		.def("setInt", &PLibForeFire::setInt)
		.def("getInt", &PLibForeFire::getInt)
		.def("getInt", &PLibForeFire::getInt)
		.def("setDouble", &PLibForeFire::setDouble)
		.def("getDouble", &PLibForeFire::getDouble)
		.def("setString", &PLibForeFire::setString)
		.def("getString", &PLibForeFire::getString)
		.def("execute", &PLibForeFire::execute)
		.def("addScalarLayer", [](PLibForeFire& self, char *type, char *name, double x0 , double y0, double t0, double width , double height, double timespan, py::array_t<int> values) {
			size_t nn[] = {1,1,1,1};
			const long* shape = values.shape();

			for (ssize_t i = 0; i < values.ndim(); i += 1) {
				nn[i] = (size_t)*shape;
				std::cout << (size_t)*shape << std::endl;
				++shape;
			}

			return self.addScalarLayer(type, name, x0, y0, t0, width, height, timespan, nn[0], nn[1], nn[2], nn[3], values);
		})
		.def("addIndexLayer", [](PLibForeFire& self, char *type, char *name, double x0 , double y0, double t0, double width , double height, double timespan, py::array_t<int> values) {
			size_t nn[] = {1,1,1,1};
			const long* shape = values.shape();

			for (ssize_t i = 0; i < values.ndim(); i += 1) {
				nn[i] = (size_t)*shape;
				std::cout << (size_t)*shape << std::endl;
				++shape;
			}

			return self.addIndexLayer(type, name, x0, y0, t0, width, height, timespan, nn[0], nn[1], nn[2], nn[3], values);
		})
		.def("getDoubleArray", [](PLibForeFire& self, char* name) {
			return self.getDoubleArray(name);
		});
}