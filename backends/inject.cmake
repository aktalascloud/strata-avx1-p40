# Called after project(strata); add optional targets only after the reviewed core is complete.
if(NOT PROJECT_NAME STREQUAL "strata" OR NOT EXISTS "${STRATA_BACKENDS_DIR}/CMakeLists.txt")
  message(FATAL_ERROR "Optional-backend injection requires the reviewed Strata project")
endif()
cmake_language(DEFER CALL include "${STRATA_BACKENDS_DIR}/CMakeLists.txt")
